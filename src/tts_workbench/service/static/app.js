"use strict";
(() => {
  const $ = (id) => document.getElementById(id);
  const form = $("synthesis-form"),
    prompt = $("prompt"),
    model = $("model");
  const generate = $("generate"),
    player = $("player");
  let config,
    models = [],
    ready = null,
    busy = false,
    results = [],
    selected = null;
  let validation = 0,
    inputValid = false,
    pollTimer,
    pollBusy = false;
  const errors = {
    invalid_request:
      "Check the text and settings. Vietnamese testing requires the exact approved external prompt.",
    unknown_or_unapproved_model:
      "This voice is unavailable. Refresh the page to reload the model list.",
    service_not_ready:
      "The service is not ready. Check the connection status and server setup.",
    queue_full:
      "The workbench is busy with other requests. Wait, then choose Generate again.",
    deadline_timeout:
      "This request expired before generation began. Try again when the workbench is free.",
    dependency_unavailable:
      "Speech dependencies are missing. Install the mms extra and restart the service.",
    device_unavailable:
      "That device is unavailable. Try Automatic or CPU in Advanced settings.",
    model_load_failure:
      "The voice could not be loaded. Check model access, your connection, and available memory before trying again.",
    synthesis_failure:
      "Speech generation failed. Try a shorter sentence and the default settings.",
    invalid_waveform:
      "The model returned invalid audio. Try again with the default settings.",
    artifact_boundary_failure:
      "The output directory is unavailable. Check the external artifact directory and restart.",
    artifact_write_failure:
      "The audio could not be saved. Check disk space and output-directory permissions.",
    artifact_collision:
      "The output name was already in use. Choose Generate again for a new result.",
    result_unavailable:
      "This result is unavailable or has expired from the server session. Generate a new clip.",
    browser_request_rejected:
      "Open the exact local dashboard URL printed by the server.",
  };
  const fetchLocal = (url, options = {}) =>
    fetch(url, { cache: "no-store", credentials: "omit", ...options });
  function showError(message) {
    $("error").textContent = message;
    $("error").hidden = !message;
  }
  function selectedModel() {
    return models.find((entry) => entry.model_id === model.value);
  }
  function label(entry) {
    return (
      { eng: "English", vie: "Vietnamese" }[entry?.documented_language_tag] ||
      entry?.model_id ||
      "Voice"
    );
  }
  function updateButton() {
    generate.disabled =
      busy ||
      !inputValid ||
      !ready?.admission_ready ||
      !ready?.artifact_root_ready ||
      !ready?.core_environment_ready ||
      !ready?.optional_runtime_ready;
  }
  async function validate() {
    const revision = ++validation;
    const text = prompt.value.trim(),
      length = [...text].length;
    const maximum = config?.max_input_characters || 500;
    $("count").textContent = `${length} / ${maximum}`;
    $("count").classList.toggle("invalid", length > maximum);
    inputValid = false;
    updateButton();
    let valid =
      !!config && !!selectedModel() && length > 0 && length <= maximum;
    const seed = Number($("seed").value);
    valid =
      valid &&
      $("seed").value !== "" &&
      Number.isSafeInteger(seed) &&
      seed >= 0;
    const speed = Number($("speed").value);
    valid =
      valid &&
      speed >= config?.speaking_rate_min &&
      speed <= config?.speaking_rate_max;
    if (valid && selectedModel().documented_language_tag === "vie") {
      const digest = await crypto.subtle.digest(
        "SHA-256",
        new TextEncoder().encode(text),
      );
      const hash = Array.from(new Uint8Array(digest), (byte) =>
        byte.toString(16).padStart(2, "0"),
      ).join("");
      valid = hash === config.vietnamese_prompt_sha256;
    }
    if (revision !== validation) return;
    inputValid = valid;
    updateButton();
  }
  function updateModel() {
    const entry = selectedModel(),
      vietnamese = entry?.documented_language_tag === "vie";
    $("example").disabled = !entry || vietnamese || busy;
    $("model-note").textContent = vietnamese
      ? "Vietnamese testing requires the exact externally reviewed prompt. Paste it after following docs/m7_reproduction.md; other text is unavailable for this voice."
      : `${label(entry)} · Local noncommercial use · Custom text is unreviewed.`;
    validate();
  }
  async function refreshStatus() {
    if (pollBusy) return;
    pollBusy = true;
    try {
      const response = await fetchLocal("/ready", {
        signal: AbortSignal.timeout(10000),
      });
      const payload = await response.json();
      if (!payload.queue) throw new Error("unavailable");
      ready = payload;
      const canRun = ready.status === "ready" && ready.optional_runtime_ready;
      $("connection-dot").className = `dot ${canRun ? "" : "pending"}`;
      $("connection-title").textContent = canRun
        ? "Connected · Ready for speech"
        : "Connected · Setup needed";
      $("connection-detail").textContent = !ready.artifact_root_ready
        ? "Set an existing external TTS_WORKBENCH_ARTIFACT_ROOT and restart the service."
        : !ready.core_environment_ready
          ? "The core environment is not ready. Check the server setup."
          : !ready.optional_runtime_ready
            ? "Install the mms extra in your environment, then restart the service."
            : !ready.admission_ready
              ? "The service is shutting down or cannot accept new work."
              : `${ready.model_loaded ? "A voice is loaded." : "Your first request will load the voice and may download it."} ${ready.queue.active_requests} active · ${ready.queue.pending_requests} waiting across the service.`;
    } catch {
      ready = null;
      $("connection-dot").className = "dot offline";
      $("connection-title").textContent = "Connection unavailable";
      $("connection-detail").textContent =
        "Start the local service, then check the connection again. An active request may still be running.";
    } finally {
      pollBusy = false;
      updateButton();
    }
  }
  function resetPlayer() {
    player.pause();
    player.removeAttribute("src");
    player.load();
    $("download").removeAttribute("href");
  }
  function renderHistory() {
    $("history").replaceChildren();
    for (const item of results) {
      const li = document.createElement("li"),
        button = document.createElement("button");
      button.type = "button";
      button.setAttribute("aria-current", String(item.id === selected));
      const play = document.createElement("span");
      play.textContent = "▶";
      play.setAttribute("aria-hidden", "true");
      const text = document.createElement("span"),
        title = document.createElement("strong"),
        detail = document.createElement("small");
      title.textContent = `${item.name} · Clip ${item.number}`;
      detail.textContent = `${item.meta.duration_seconds.toFixed(1)}s · ${item.meta.speaking_rate.toFixed(2)}× · ${item.meta.device.toUpperCase()}`;
      text.append(title, detail);
      const time = document.createElement("time");
      time.textContent = item.time;
      button.append(play, text, time);
      button.addEventListener("click", () => selectResult(item));
      li.append(button);
      $("history").append(li);
    }
    $("clear").disabled = !results.length;
  }
  function selectResult(item) {
    resetPlayer();
    selected = item.id;
    $("empty-result").hidden = true;
    $("current-result").hidden = false;
    $("result-title").textContent = `${item.name} · Clip ${item.number}`;
    $("result-time").textContent = item.time;
    $("result-summary").textContent =
      `${item.meta.duration_seconds.toFixed(1)} seconds · ${item.meta.sample_rate.toLocaleString()} Hz · ${item.meta.device.toUpperCase()}`;
    player.src = `/v1/runs/${item.id}/audio`;
    $("download").href = `/v1/runs/${item.id}/audio?download=true`;
    $("metadata").replaceChildren();
    const entries = {
      Model: item.meta.model_id,
      Seed: item.meta.seed,
      "Speaking speed": `${item.meta.speaking_rate.toFixed(2)}×`,
      "Model loading": `${item.meta.model_load_seconds.toFixed(2)}s`,
      Synthesis: `${item.meta.synthesis_seconds.toFixed(2)}s`,
      Prompt: item.meta.prompt_provenance.replaceAll("_", " "),
      "Language quality": "Not evaluated",
    };
    for (const [key, value] of Object.entries(entries)) {
      const dt = document.createElement("dt"),
        dd = document.createElement("dd");
      dt.textContent = key;
      dd.textContent = String(value);
      $("metadata").append(dt, dd);
    }
    renderHistory();
  }
  let clipNumber = 0;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (busy || generate.disabled) return;
    busy = true;
    showError("");
    updateButton();
    const entry = selectedModel();
    const request = {
      model_id: model.value,
      text: prompt.value.trim(),
      requested_device: $("device").value,
      seed: Number($("seed").value),
      generation_settings: { speaking_rate: Number($("speed").value) },
    };
    for (const id of ["model", "prompt", "example", "device", "seed", "speed"])
      $(id).disabled = true;
    generate.classList.add("busy");
    generate.textContent = "Generating speech…";
    const started = performance.now();
    const progress = () => {
      $("progress").textContent =
        `Waiting for your audio · ${Math.floor((performance.now() - started) / 1000)}s elapsed. First use may download and load the voice.`;
    };
    progress();
    const timer = setInterval(progress, 1000);
    let completed = false;
    try {
      const response = await fetchLocal("/v1/synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      });
      const payload = await response.json();
      if (!response.ok) {
        showError(
          errors[payload.category] ||
            "Generation failed. Check the local service and try again.",
        );
        $("progress").textContent = "No audio result was returned.";
        return;
      }
      completed = true;
      const metadata = await fetchLocal(`/v1/runs/${payload.run_id}`, {
        signal: AbortSignal.timeout(15000),
      });
      if (!metadata.ok) throw new Error("result unavailable");
      const item = {
        id: payload.run_id,
        name: label(entry),
        number: ++clipNumber,
        time: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        meta: await metadata.json(),
      };
      results.unshift(item);
      results = results.slice(0, config.history_limit);
      selectResult(item);
      $("progress").textContent = "Your audio is ready. Press play to listen.";
    } catch {
      showError(
        completed
          ? "Speech was generated, but playback is unavailable. The saved audio remains in your external artifact directory."
          : "The connection ended before a result arrived. Generation may still be running; check the service before starting another request. Nothing was retried automatically.",
      );
      $("progress").textContent = completed
        ? "Generation completed; playback unavailable."
        : "Result unknown. Check the connection.";
    } finally {
      clearInterval(timer);
      busy = false;
      for (const id of ["model", "prompt", "device", "seed", "speed"])
        $(id).disabled = false;
      generate.classList.remove("busy");
      generate.textContent = "▶ Generate speech";
      updateModel();
      refreshStatus();
    }
  });
  player.addEventListener("error", () => {
    if (player.getAttribute("src")) showError(errors.result_unavailable);
  });
  prompt.addEventListener("input", validate);
  model.addEventListener("change", updateModel);
  $("seed").addEventListener("input", validate);
  $("speed").addEventListener("input", () => {
    $("speed-value").value = `${Number($("speed").value).toFixed(2)}×`;
    validate();
  });
  $("example").addEventListener("click", () => {
    prompt.value = config.english_example;
    prompt.focus();
    validate();
  });
  $("reconnect").addEventListener("click", () => {
    if (!config || !models.length) initialize();
    else refreshStatus();
  });
  function clearResults() {
    resetPlayer();
    results = [];
    selected = null;
    renderHistory();
    $("empty-result").hidden = false;
    $("current-result").hidden = true;
  }
  $("clear").addEventListener("click", clearResults);
  window.addEventListener("pagehide", () => {
    prompt.value = "";
    clearResults();
    clearInterval(pollTimer);
  });
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) {
      validate();
      refreshStatus();
      pollTimer = setInterval(refreshStatus, 5000);
    }
  });
  async function initialize() {
    try {
      const responses = await Promise.all(
        ["/v1/ui-config", "/v1/models"].map((url) =>
          fetchLocal(url, { signal: AbortSignal.timeout(10000) }),
        ),
      );
      if (responses.some((response) => !response.ok))
        throw new Error("setup unavailable");
      config = await responses[0].json();
      models = (await responses[1].json()).models;
      model.replaceChildren();
      for (const entry of models) {
        const option = document.createElement("option");
        option.value = entry.model_id;
        option.textContent = `${label(entry)} — ${entry.model_id}`;
        model.append(option);
      }
      model.value =
        (
          models.find((entry) => entry.documented_language_tag === "eng") ||
          models[0]
        )?.model_id || "";
      model.disabled = !models.length;
      updateModel();
      showError("");
    } catch {
      showError(
        "Could not load the local model list. Start the service, then check the connection again.",
      );
    }
    await refreshStatus();
    clearInterval(pollTimer);
    pollTimer = setInterval(refreshStatus, 5000);
  }
  initialize();
})();
