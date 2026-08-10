(function () {
  "use strict";

  const STORAGE_KEY = "pastor-sermon-ai.setup-companion.v1";
  const STORAGE_SCHEMA = 1;
  const VALID_STAGES = new Set([
    "choose-os",
    "unknown-os",
    "unsupported-os",
    "load-message",
    "copy-message",
    "open-chatgpt",
    "confirm-chatgpt",
    "paste-message"
  ]);
  const VALID_OS = new Set(["mac", "windows"]);

  const releaseConfig = Object.assign(
    {
      releaseMetadataUrl: "../RELEASE.json",
      chatgptUrl: "https://chatgpt.com/",
      pluginName: "Sermon Slide Builder",
      pluginVersion: "0.1.0"
    },
    window.PASTOR_SETUP_CONFIG || {}
  );

  const elements = {
    actionStage: document.getElementById("action-stage"),
    configurationAlert: document.getElementById("configuration-alert"),
    configurationMessage: document.getElementById("configuration-message"),
    deviceName: document.getElementById("device-name"),
    deviceSymbol: document.getElementById("device-symbol"),
    saveStateLabel: document.getElementById("save-state-label"),
    saveIndicator: document.getElementById("save-indicator"),
    statusStrip: document.getElementById("status-strip"),
    themeColor: document.getElementById("theme-color"),
    titlebarName: document.querySelector(".titlebar-name"),
    openHelp: document.getElementById("open-help"),
    helpDialog: document.getElementById("help-dialog"),
    helpForm: document.getElementById("help-form"),
    helpQuestion: document.getElementById("help-question"),
    helpError: document.getElementById("help-error"),
    helpCopyStatus: document.getElementById("help-copy-status"),
    helpOs: document.getElementById("help-os"),
    helpStep: document.getElementById("help-step"),
    questionCount: document.getElementById("question-count"),
    chatgptFallback: document.getElementById("chatgpt-fallback"),
    openReset: document.getElementById("open-reset"),
    resetDialog: document.getElementById("reset-dialog"),
    confirmReset: document.getElementById("confirm-reset"),
    toast: document.getElementById("toast"),
    toastMessage: document.getElementById("toast-message")
  };

  let storageWorks = canUseLocalStorage();
  let state = loadState();
  let toastTimer = null;
  let renderTimer = null;
  let trustedSetupMessage = null;
  let messageImportError = "";
  let releaseMetadata = null;
  let releaseLoadError = "";
  let isReleaseConfigured = false;

  const stageNames = {
    "choose-os": "Choose a computer",
    "unknown-os": "Identify this computer",
    "unsupported-os": "Use a supported computer",
    "load-message": "Choose the church setup message",
    "copy-message": "Copy the setup message",
    "open-chatgpt": "Open ChatGPT",
    "confirm-chatgpt": "Confirm ChatGPT opened",
    "paste-message": "Paste the copied message"
  };

  const osNames = {
    mac: "Mac",
    windows: "Windows"
  };

  const chatgptUrl = getSafeChatgptUrl(releaseConfig.chatgptUrl);

  function canUseLocalStorage() {
    try {
      const key = STORAGE_KEY + ".test";
      window.localStorage.setItem(key, "1");
      window.localStorage.removeItem(key);
      return true;
    } catch (_error) {
      return false;
    }
  }

  function createDefaultState() {
    return {
      schemaVersion: STORAGE_SCHEMA,
      os: null,
      stage: "choose-os"
    };
  }

  function normalizeState(candidate) {
    const normalized = createDefaultState();

    if (!candidate || typeof candidate !== "object") {
      return normalized;
    }

    if (VALID_OS.has(candidate.os)) {
      normalized.os = candidate.os;
    }

    if (VALID_STAGES.has(candidate.stage)) {
      normalized.stage = candidate.stage;
    }

    if (!normalized.os) {
      normalized.stage = "choose-os";
    } else if (normalized.stage === "choose-os") {
      normalized.stage = "load-message";
    } else if (
      normalized.stage === "copy-message" ||
      normalized.stage === "open-chatgpt" ||
      normalized.stage === "confirm-chatgpt" ||
      normalized.stage === "paste-message"
    ) {
      // The external message, its ZIP checksum, and clipboard state are never
      // persisted. After a reload, require the pastor to load and copy again.
      normalized.stage = "load-message";
    }

    return normalized;
  }

  function loadState() {
    if (!storageWorks) {
      return createDefaultState();
    }

    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (!stored) {
        return createDefaultState();
      }
      return normalizeState(JSON.parse(stored));
    } catch (_error) {
      try {
        window.localStorage.removeItem(STORAGE_KEY);
      } catch (_removeError) {
        storageWorks = false;
      }
      return createDefaultState();
    }
  }

  function saveState() {
    if (!storageWorks) {
      updateSaveLabels();
      return;
    }

    try {
      window.localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          schemaVersion: STORAGE_SCHEMA,
          os: state.os,
          stage: state.stage
        })
      );
    } catch (_error) {
      storageWorks = false;
    }

    updateSaveLabels();
  }

  function releaseIsConfigured(metadata) {
    if (!metadata || typeof metadata !== "object") {
      return false;
    }

    const publisher = String(metadata.publisher || "").trim();
    const releaseUrl = String(metadata.releaseUrl || "").trim();
    const gitCommit = String(metadata.gitCommit || "").trim();
    const packageVersion = String(metadata.packageVersion || "").trim();
    const releaseTag = String(metadata.releaseTag || "").trim();
    const messageTemplate = String(metadata.messageTemplate || "");
    const combined = publisher + releaseUrl + gitCommit + packageVersion + releaseTag;
    const templateMarkers = (messageTemplate.match(/\{\{[^}]+\}\}/g) || [])
      .sort()
      .join("|");
    const expectedMarkers = [
      "{{GITHUB_RELEASE_URL}}",
      "{{GIT_COMMIT_SHA}}",
      "{{RELEASE_ZIP_SHA256}}"
    ].sort().join("|");

    if (
      publisher !== "Valley Forge Baptist" ||
      /\{\{[^}]+\}\}/.test(combined) ||
      !/^[0-9a-fA-F]{40}$/.test(gitCommit) ||
      packageVersion !== String(releaseConfig.pluginVersion) ||
      releaseTag !== "v" + packageVersion ||
      templateMarkers !== expectedMarkers
    ) {
      return false;
    }

    try {
      const url = new URL(releaseUrl);
      const parts = url.pathname.split("/").filter(Boolean).map(decodeURIComponent);
      return url.protocol === "https:" &&
        url.hostname === "github.com" &&
        parts.length === 5 &&
        parts[2] === "releases" &&
        parts[3] === "tag" &&
        parts[4] === releaseTag;
    } catch (_error) {
      return false;
    }
  }

  function normalizeReleaseMetadata(value) {
    if (!value || typeof value !== "object") {
      return null;
    }

    return {
      publisher: String(value.publisher || "").trim(),
      releaseUrl: String(value.releaseUrl || value.release_url || "").trim(),
      gitCommit: String(value.gitCommit || value.git_commit || "").trim().toLowerCase(),
      packageVersion: String(value.packageVersion || value.package_version || "").trim(),
      releaseTag: String(value.releaseTag || value.release_tag || "").trim(),
      messageTemplate: String(value.messageTemplate || value.message_template || "")
    };
  }

  async function loadReleaseMetadata() {
    const fallback = normalizeReleaseMetadata(
      window.PASTOR_SERMON_RELEASE || window.PASTOR_RELEASE_METADATA
    );
    let fetched = null;

    try {
      const metadataUrl = new URL(releaseConfig.releaseMetadataUrl || "../RELEASE.json", window.location.href);
      const response = await window.fetch(metadataUrl.href, { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Release metadata returned " + response.status + ".");
      }
      fetched = normalizeReleaseMetadata(await response.json());
      if (!fetched) {
        throw new Error("Release metadata was not readable.");
      }
      if (!fetched.messageTemplate && fallback && fallback.messageTemplate) {
        fetched.messageTemplate = fallback.messageTemplate;
      }
    } catch (_error) {
      releaseLoadError = "RELEASE.json could not be read in this browser.";
    }

    releaseMetadata = fetched || fallback;
    isReleaseConfigured = releaseIsConfigured(releaseMetadata);

    if (!isReleaseConfigured && !releaseLoadError) {
      releaseLoadError = "RELEASE.json still contains placeholder or invalid release values.";
    }
  }

  function getSafeChatgptUrl(value) {
    try {
      const url = new URL(String(value));
      if (url.protocol === "https:" || url.protocol === "http:") {
        return url.href;
      }
    } catch (_error) {
      // Use the known ChatGPT URL below.
    }
    return "https://chatgpt.com/";
  }

  function setupMessage() {
    if (!trustedSetupMessage) {
      return "";
    }

    const computer = state.os === "windows" ? "Windows" : "Mac";
    return trustedSetupMessage.trimEnd() + "\n\nComputer selected in setup launcher: " + computer + "\n";
  }

  function svgUse(id, className) {
    const classAttribute = className ? ' class="' + className + '"' : "";
    return '<svg' + classAttribute + ' aria-hidden="true"><use href="#' + id + '"></use></svg>';
  }

  function macIcon() {
    return [
      '<svg aria-hidden="true" viewBox="0 0 28 28">',
      '<rect x="4" y="5" width="20" height="15" rx="2.5"></rect>',
      '<path d="M2.8 22h22.4M11.5 22h5"></path>',
      "</svg>"
    ].join("");
  }

  function windowsIcon() {
    return [
      '<svg aria-hidden="true" viewBox="0 0 28 28">',
      '<path d="m4 6 8.5-1.2v8.4H4V6Zm10.5-1.5L24 3.2v10h-9.5V4.5ZM4 15h8.5v8.4L4 22.2V15Zm10.5 0H24v10l-9.5-1.3V15Z"></path>',
      "</svg>"
    ].join("");
  }

  function render(options) {
    const shouldFocus = Boolean(options && options.focusHeading);
    applyTheme();
    updateDeviceSummary();
    updateSaveLabels();
    updateStatusStrip();
    updateHelpContext();
    elements.configurationAlert.hidden = isReleaseConfigured;
    elements.configurationMessage.textContent = releaseLoadError || "RELEASE.json must contain the finished publisher, tagged release URL, and full commit before this page is shared.";

    if (state.stage === "choose-os") {
      elements.actionStage.innerHTML = renderChooseOs();
    } else if (state.stage === "unknown-os") {
      elements.actionStage.innerHTML = renderUnknownOs();
    } else if (state.stage === "unsupported-os") {
      elements.actionStage.innerHTML = renderUnsupportedOs();
    } else if (state.stage === "load-message") {
      elements.actionStage.innerHTML = renderLoadMessage();
    } else if (state.stage === "copy-message") {
      elements.actionStage.innerHTML = renderCopyMessage();
    } else if (state.stage === "open-chatgpt") {
      elements.actionStage.innerHTML = renderOpenChatgpt();
    } else if (state.stage === "confirm-chatgpt") {
      elements.actionStage.innerHTML = renderConfirmChatgpt();
    } else {
      elements.actionStage.innerHTML = renderPasteMessage();
    }

    if (shouldFocus) {
      window.clearTimeout(renderTimer);
      renderTimer = window.setTimeout(function () {
        const heading = elements.actionStage.querySelector("h2");
        if (heading) {
          heading.focus({ preventScroll: true });
        }
      }, window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 90);
    }
  }

  function applyTheme() {
    document.body.dataset.osTheme = state.os === "windows" ? "windows" : "mac";
    elements.titlebarName.textContent = state.os === "windows" ? "Settings · Setup Companion" : "Setup Companion";
    elements.themeColor.content = state.os === "windows" ? "#f3f3f3" : "#f5f5f7";
  }

  function updateDeviceSummary() {
    if (state.os === "mac") {
      elements.deviceName.textContent = "Mac";
      elements.deviceSymbol.textContent = "⌘";
    } else if (state.os === "windows") {
      elements.deviceName.textContent = "Windows PC";
      elements.deviceSymbol.textContent = "⊞";
    } else {
      elements.deviceName.textContent = "Not chosen";
      elements.deviceSymbol.textContent = "—";
    }
  }

  function updateSaveLabels() {
    if (storageWorks) {
      elements.saveStateLabel.textContent = "Progress saves here";
      elements.saveIndicator.classList.remove("is-unsaved");
      elements.saveIndicator.innerHTML = '<span aria-hidden="true"></span> Saved on this device';
    } else {
      elements.saveStateLabel.textContent = "This tab only";
      elements.saveIndicator.classList.add("is-unsaved");
      elements.saveIndicator.innerHTML = '<span aria-hidden="true"></span> Keep this tab open';
    }
  }

  function updateStatusStrip() {
    const chatgptStatus = elements.statusStrip.querySelector('[data-status="chatgpt"]');
    const statusText = chatgptStatus.querySelector("small");

    chatgptStatus.setAttribute("aria-current", "step");
    if (state.stage === "choose-os" || state.stage === "unknown-os") {
      statusText.textContent = "Current";
    } else if (state.stage === "unsupported-os") {
      statusText.textContent = "Paused";
    } else if (state.stage === "load-message") {
      statusText.textContent = isReleaseConfigured ? "Trust message" : "Waiting";
    } else if (state.stage === "copy-message") {
      statusText.textContent = "Message ready";
    } else if (state.stage === "open-chatgpt") {
      statusText.textContent = "Open next";
    } else if (state.stage === "confirm-chatgpt") {
      statusText.textContent = "Checking";
    } else {
      statusText.textContent = "In ChatGPT";
    }
  }

  function updateHelpContext() {
    elements.helpOs.textContent = state.os ? osNames[state.os] : "Not chosen";
    if (!isReleaseConfigured && state.stage === "load-message") {
      elements.helpStep.textContent = "Get the finished setup page";
    } else {
      elements.helpStep.textContent = stageNames[state.stage] || stageNames["choose-os"];
    }
  }

  function renderChooseOs() {
    return [
      '<article class="action-card">',
      '<p class="step-tag">Current action</p>',
      '<h2 id="current-action-title" tabindex="-1">Are you using a Mac or a Windows computer?</h2>',
      '<p class="action-lead">Choose this computer so the setup companion can match the controls you see.</p>',
      '<div class="action-controls">',
      '<fieldset class="os-fieldset">',
      '<legend class="sr-only">Choose Mac or Windows</legend>',
      '<div class="os-options">',
      '<label class="os-choice">',
      '<input class="sr-only" type="radio" name="computer-os" value="mac" data-action="select-os">',
      '<span class="os-icon">' + macIcon() + "</span>",
      '<span><strong>Mac</strong><small>Use the macOS setup view</small></span>',
      svgUse("icon-chevron"),
      "</label>",
      '<label class="os-choice">',
      '<input class="sr-only" type="radio" name="computer-os" value="windows" data-action="select-os">',
      '<span class="os-icon">' + windowsIcon() + "</span>",
      '<span><strong>Windows</strong><small>Use the Windows 11 setup view</small></span>',
      svgUse("icon-chevron"),
      "</label>",
      "</div>",
      "</fieldset>",
      '<div class="os-support-actions">',
      '<button class="secondary-button" type="button" data-action="unknown-os">I don\'t know</button>',
      '<button class="secondary-button" type="button" data-action="unsupported-os">Something else</button>',
      "</div>",
      "</div>",
      "</article>"
    ].join("");
  }

  function renderUnknownOs() {
    return [
      '<article class="action-card">',
      '<p class="step-tag">Current question</p>',
      '<h2 id="current-action-title" tabindex="-1">Which symbol is on a key next to your space bar?</h2>',
      '<p class="action-lead">Choose the symbol you see on this computer.</p>',
      '<div class="action-controls button-row">',
      '<button class="primary-button" type="button" data-action="identified-mac">⌘ Command</button>',
      '<button class="primary-button" type="button" data-action="identified-windows">⊞ Windows</button>',
      '<button class="secondary-button" type="button" data-action="unsupported-os">Neither one</button>',
      "</div>",
      "</article>"
    ].join("");
  }

  function renderUnsupportedOs() {
    return [
      '<article class="action-card">',
      '<p class="step-tag">Setup paused</p>',
      '<h2 id="current-action-title" tabindex="-1">This setup needs a Mac or Windows computer.</h2>',
      '<p class="action-lead">No changes were made. Ask the church computer helper for a Mac or Windows computer with ChatGPT desktop and PowerPoint.</p>',
      '<div class="completion-note configuration-stop">',
      svgUse("icon-shield"),
      "<span>Setup will stay here. Ask Setup Help can help with this current question.</span>",
      "</div>",
      "</article>"
    ].join("");
  }

  function renderLoadMessage() {
    if (!isReleaseConfigured) {
      return [
        '<article class="action-card">',
        '<p class="step-tag">Current action</p>',
        '<h2 id="current-action-title" tabindex="-1">Ask for the finished setup page.</h2>',
        '<p class="action-lead">This preview does not contain finished release details, so setup is intentionally locked.</p>',
        '<div class="completion-note configuration-stop">',
        svgUse("icon-warning"),
        "<span>Nothing has been trusted or copied. Ask the church setup owner for the completed release package and setup message.</span>",
        "</div>",
        "</article>"
      ].join("");
    }

    return [
      '<article class="action-card">',
      '<p class="step-tag">Current action</p>',
      '<h2 id="current-action-title" tabindex="-1">Choose the church setup message.</h2>',
      '<p class="action-lead">Select <strong>PASTOR-SETUP-MESSAGE.txt</strong> from the church setup owner.</p>',
      '<div class="action-controls">',
      '<div class="release-identity" aria-label="Expected release identity">',
      '<span><small>Publisher</small><strong>' + escapeHtml(releaseMetadata.publisher) + "</strong></span>",
      '<span><small>Tagged release</small><strong>' + escapeHtml(shortReleaseName(releaseMetadata.releaseUrl)) + "</strong></span>",
      '<span><small>Commit</small><strong>' + escapeHtml(shortCommit(releaseMetadata.gitCommit)) + "</strong></span>",
      "</div>",
      '<label class="primary-button file-button">',
      svgUse("icon-pin"),
      "Choose setup message",
      '<input type="file" accept=".txt,text/plain" data-action="load-setup-message">',
      "</label>",
      '<p class="import-error" id="import-error" role="alert">' + escapeHtml(messageImportError) + "</p>",
      "</div>",
      "</article>"
    ].join("");
  }

  function renderCopyMessage() {
    if (!isReleaseConfigured || !trustedSetupMessage) {
      state.stage = "load-message";
      return renderLoadMessage();
    }

    return [
      '<article class="action-card">',
      '<p class="step-tag">Current action</p>',
      '<h2 id="current-action-title" tabindex="-1">Copy the pinned setup message.</h2>',
      '<p class="action-lead">This message tells ChatGPT to handle computer and plugin setup one action at a time.</p>',
      '<div class="action-controls">',
      '<div class="trusted-message-label">',
      svgUse("icon-shield"),
      '<span><strong>Matching setup message loaded</strong><small>The complete message matches this release package. The ZIP itself is not verified yet.</small></span>',
      "</div>",
      '<div class="pinned-message">',
      '<div class="pinned-header">' + svgUse("icon-pin") + "Pinned setup message</div>",
      "<pre>" + escapeHtml(setupMessage()) + "</pre>",
      "</div>",
      '<div class="button-row">',
      '<button class="primary-button" type="button" data-action="copy-setup">',
      svgUse("icon-copy"),
      "Copy setup message",
      "</button>",
      "</div>",
      '<p class="copy-error" id="copy-error" role="alert"></p>',
      "</div>",
      "</article>"
    ].join("");
  }

  function shortReleaseName(value) {
    try {
      const url = new URL(value);
      const pieces = url.pathname.split("/").filter(Boolean);
      return pieces.length >= 5 ? pieces.slice(-3).join(" / ") : url.pathname;
    } catch (_error) {
      return value;
    }
  }

  function shortCommit(value) {
    return value ? value.slice(0, 10) + "…" + value.slice(-6) : "Not configured";
  }

  function parseTrustedSetupMessage(text) {
    const normalized = String(text || "").replace(/\r\n?/g, "\n").trim();
    if (!normalized || /\{\{[^}]+\}\}/.test(normalized)) {
      throw new Error("This setup message is unfinished. Ask the church setup owner for the generated PASTOR-SETUP-MESSAGE.txt file.");
    }

    const publisherLines = normalized.match(/^Publisher:.*$/gm) || [];
    const releaseLines = normalized.match(/^Tagged release:.*$/gm) || [];
    const commitLines = normalized.match(/^Git commit:.*$/gm) || [];
    const zipHashLines = normalized.match(/^Release ZIP SHA-256:.*$/gm) || [];

    if (
      publisherLines.length !== 1 ||
      releaseLines.length !== 1 ||
      commitLines.length !== 1 ||
      zipHashLines.length !== 1
    ) {
      throw new Error("The setup message has missing or repeated release details. Ask the church setup owner for the generated message.");
    }

    const publisherMatch = publisherLines[0].match(/^Publisher:\s*(.+)$/);
    const releaseMatch = releaseLines[0].match(/^Tagged release:\s*(\S+)\s*$/);
    const commitMatch = commitLines[0].match(/^Git commit:\s*([0-9a-fA-F]+)\s*$/);
    const zipHashMatch = zipHashLines[0].match(/^Release ZIP SHA-256:\s*([0-9a-fA-F]+)\s*$/);

    if (!publisherMatch || !releaseMatch || !commitMatch || !zipHashMatch) {
      throw new Error("This is not the generated pastor setup message. Ask the church setup owner for PASTOR-SETUP-MESSAGE.txt.");
    }

    if (publisherMatch[1].trim() !== "Valley Forge Baptist") {
      throw new Error("The publisher does not match Valley Forge Baptist. Ask the church setup owner for the correct message.");
    }

    if (releaseMatch[1].trim() !== releaseMetadata.releaseUrl) {
      throw new Error("The tagged release does not match this setup package. Ask the church setup owner for the matching message.");
    }

    if (!/^[0-9a-fA-F]{40}$/.test(commitMatch[1]) || commitMatch[1].toLowerCase() !== releaseMetadata.gitCommit.toLowerCase()) {
      throw new Error("The full Git commit does not match this setup package. Ask the church setup owner for the matching message.");
    }

    if (!/^[0-9a-fA-F]{64}$/.test(zipHashMatch[1])) {
      throw new Error("The release ZIP checksum is not complete. Ask the church setup owner for the generated message.");
    }

    const expectedMessage = releaseMetadata.messageTemplate
      .replace("{{GITHUB_RELEASE_URL}}", releaseMetadata.releaseUrl)
      .replace("{{GIT_COMMIT_SHA}}", releaseMetadata.gitCommit)
      .replace("{{RELEASE_ZIP_SHA256}}", zipHashMatch[1].toLowerCase())
      .replace(/\r\n?/g, "\n")
      .trim();

    if (normalized !== expectedMessage) {
      throw new Error("The full setup message does not match this release package. Ask the church setup owner for the original generated message.");
    }

    return normalized + "\n";
  }

  function renderOpenChatgpt() {
    return [
      '<article class="action-card">',
      '<p class="step-tag">Current action</p>',
      '<div class="handoff-visual">' + svgUse("icon-arrow-up-right") + "</div>",
      '<h2 id="current-action-title" tabindex="-1">Open ChatGPT.</h2>',
      '<p class="action-lead">Your setup message is copied and ready.</p>',
      '<div class="action-controls">',
      '<a class="primary-button" data-action="open-chatgpt" href="' + escapeAttribute(chatgptUrl) + '" target="_blank" rel="noopener noreferrer">',
      "Open ChatGPT",
      svgUse("icon-arrow-up-right"),
      "</a>",
      "</div>",
      '<div class="completion-note">' + svgUse("icon-check") + "<span>The setup message is on your clipboard.</span></div>",
      "</article>"
    ].join("");
  }

  function renderPasteMessage() {
    return [
      '<article class="action-card">',
      '<p class="step-tag">Current action</p>',
      '<div class="handoff-visual">' + svgUse("icon-copy") + "</div>",
      '<h2 id="current-action-title" tabindex="-1">Paste the copied message into ChatGPT.</h2>',
      '<p class="action-lead">ChatGPT will take over from there and show only one setup action at a time.</p>',
      '<div class="completion-note">',
      svgUse("icon-shield"),
      "<span>Keep passwords, verification codes, API keys, and private church files out of chat.</span>",
      "</div>",
      "</article>"
    ].join("");
  }

  function renderConfirmChatgpt() {
    return [
      '<article class="action-card">',
      '<p class="step-tag">Current question</p>',
      '<h2 id="current-action-title" tabindex="-1">Did ChatGPT open in a new tab?</h2>',
      '<p class="action-lead">Choose one answer.</p>',
      '<div class="action-controls button-row">',
      '<button class="primary-button" type="button" data-action="chatgpt-opened">Yes, it opened</button>',
      '<button class="secondary-button" type="button" data-action="chatgpt-not-opened">No, it did not</button>',
      "</div>",
      "</article>"
    ].join("");
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function escapeAttribute(value) {
    return escapeHtml(value).replace(/`/g, "&#096;");
  }

  async function copyText(value) {
    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(value);
        return true;
      } catch (_error) {
        // Try the offline-compatible fallback below.
      }
    }

    const textarea = document.createElement("textarea");
    textarea.value = value;
    textarea.setAttribute("readonly", "");
    textarea.setAttribute("aria-hidden", "true");
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    textarea.style.top = "0";
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();

    let copied = false;
    try {
      copied = document.execCommand("copy");
    } catch (_error) {
      copied = false;
    }
    textarea.remove();
    return copied;
  }

  function showToast(message) {
    window.clearTimeout(toastTimer);
    elements.toastMessage.textContent = message;
    elements.toast.hidden = false;
    toastTimer = window.setTimeout(function () {
      elements.toast.hidden = true;
    }, 3600);
  }

  function showHelpDialog() {
    updateHelpContext();
    elements.helpError.textContent = "";
    elements.helpCopyStatus.hidden = true;
    elements.helpQuestion.removeAttribute("aria-invalid");
    elements.chatgptFallback.hidden = true;
    elements.helpDialog.showModal();
    window.setTimeout(function () {
      elements.helpQuestion.focus();
    }, 0);
  }

  function helpPrompt(question) {
    const repository = isReleaseConfigured ? releaseMetadata.releaseUrl : "not configured in this preview";
    const os = state.os ? osNames[state.os] : "not chosen yet";
    const currentAction = !isReleaseConfigured && state.stage === "load-message"
      ? "Get the finished setup page"
      : stageNames[state.stage] || stageNames["choose-os"];

    return [
      "I need help with Pastor Sermon AI computer setup.",
      "Repository: " + repository,
      "Computer: " + os,
      "Current action: " + currentAction,
      "",
      "What is stopping me:",
      question,
      "",
      "Read SETUP-ASSISTANT.md if the repository is available. Help me with only this current action.",
      "Give me one small action, then wait for DONE. Do not move to a later step.",
      "Do not ask for passwords, verification codes, API keys, sermon files, church-member photos, or private church files.",
      "Do not tell me to turn off security protections."
    ].join("\n");
  }

  function showManualCopyRecovery(prompt) {
    let recovery = document.getElementById("manual-copy-recovery");
    if (!recovery) {
      recovery = document.createElement("div");
      recovery.id = "manual-copy-recovery";
      recovery.className = "manual-copy-recovery";
      recovery.innerHTML = [
        '<label for="manual-help-prompt">Press <span class="mac-copy-key">Command+C</span><span class="windows-copy-key">Ctrl+C</span> to copy the selected prompt.</label>',
        '<textarea id="manual-help-prompt" readonly rows="5"></textarea>',
        '<button class="secondary-button" id="confirm-manual-help-copy" type="button">I copied the help prompt</button>'
      ].join("");
      elements.helpForm.appendChild(recovery);
    }

    const textarea = recovery.querySelector("textarea");
    textarea.value = prompt;
    recovery.hidden = false;
    textarea.focus();
    textarea.select();
  }

  elements.actionStage.addEventListener("change", async function (event) {
    const control = event.target.closest("[data-action]");
    if (!control) {
      return;
    }

    if (control.dataset.action === "select-os") {
      if (!VALID_OS.has(control.value)) {
        return;
      }

      state.os = control.value;
      state.stage = "load-message";
      trustedSetupMessage = null;
      messageImportError = "";
      saveState();
      render({ focusHeading: true });
      showToast(osNames[state.os] + " view selected");
      return;
    }

    if (control.dataset.action === "load-setup-message") {
      const file = control.files && control.files[0];
      if (!file) {
        return;
      }

      const errorElement = elements.actionStage.querySelector("#import-error");
      trustedSetupMessage = null;
      messageImportError = "";

      try {
        if (file.name !== "PASTOR-SETUP-MESSAGE.txt") {
          throw new Error("Choose the file named PASTOR-SETUP-MESSAGE.txt from the church setup owner.");
        }
        if (file.size > 64 * 1024) {
          throw new Error("That setup message is unexpectedly large. Ask the church setup owner for the generated text file.");
        }

        trustedSetupMessage = parseTrustedSetupMessage(await file.text());
      } catch (error) {
        messageImportError = error && error.message
          ? error.message
          : "The setup message could not be read. Ask the church setup owner for the generated text file.";
        control.value = "";
        if (errorElement) {
          errorElement.textContent = messageImportError;
        }
        return;
      }

      state.stage = "copy-message";
      saveState();
      render({ focusHeading: true });
      showToast("Matching setup message loaded");
    }
  });

  elements.actionStage.addEventListener("click", async function (event) {
    const control = event.target.closest("[data-action]");
    if (!control) {
      return;
    }

    const action = control.dataset.action;

    if (action === "unknown-os") {
      state.stage = "unknown-os";
      render({ focusHeading: true });
      return;
    }

    if (action === "unsupported-os") {
      state.stage = "unsupported-os";
      render({ focusHeading: true });
      return;
    }

    if (action === "identified-mac" || action === "identified-windows") {
      state.os = action === "identified-mac" ? "mac" : "windows";
      state.stage = "load-message";
      saveState();
      render({ focusHeading: true });
      showToast(osNames[state.os] + " view selected");
      return;
    }

    if (action === "copy-setup") {
      event.preventDefault();
      if (!isReleaseConfigured || !trustedSetupMessage) {
        return;
      }

      control.disabled = true;
      const copied = await copyText(setupMessage());
      control.disabled = false;

      if (!copied) {
        const error = elements.actionStage.querySelector("#copy-error");
        if (error) {
          error.textContent = "Automatic copy was blocked. Use the one manual copy action below.";
        }
        showManualSetupCopyRecovery();
        return;
      }

      state.stage = "open-chatgpt";
      saveState();
      render({ focusHeading: true });
      showToast("Setup message copied");
      return;
    }

    if (action === "open-chatgpt") {
      state.stage = "confirm-chatgpt";
      saveState();
      window.setTimeout(function () {
        render({ focusHeading: true });
      }, 120);
      return;
    }

    if (action === "confirm-manual-setup-copy") {
      state.stage = "open-chatgpt";
      saveState();
      render({ focusHeading: true });
      showToast("Manual copy confirmed");
      return;
    }

    if (action === "chatgpt-opened") {
      state.stage = "paste-message";
      saveState();
      render({ focusHeading: true });
      return;
    }

    if (action === "chatgpt-not-opened") {
      state.stage = "open-chatgpt";
      saveState();
      render({ focusHeading: true });
      showToast("Try opening ChatGPT again");
    }
  });

  function showManualSetupCopyRecovery() {
    if (document.getElementById("manual-setup-copy-recovery")) {
      return;
    }
    const recovery = document.createElement("div");
    recovery.id = "manual-setup-copy-recovery";
    recovery.className = "manual-copy-recovery";

    const label = document.createElement("label");
    label.htmlFor = "manual-setup-message";
    label.textContent = state.os === "windows"
      ? "Press Ctrl+C to copy the selected setup message."
      : "Press Command+C to copy the selected setup message.";

    const textarea = document.createElement("textarea");
    textarea.id = "manual-setup-message";
    textarea.readOnly = true;
    textarea.rows = 5;
    textarea.value = setupMessage();

    const confirm = document.createElement("button");
    confirm.type = "button";
    confirm.className = "secondary-button";
    confirm.dataset.action = "confirm-manual-setup-copy";
    confirm.textContent = "I copied the setup message";

    recovery.append(label, textarea, confirm);
    elements.actionStage.querySelector(".action-controls").appendChild(recovery);
    textarea.focus();
    textarea.select();
  }

  elements.openHelp.addEventListener("click", showHelpDialog);

  elements.openReset.addEventListener("click", function () {
    elements.resetDialog.showModal();
  });

  elements.confirmReset.addEventListener("click", function () {
    if (storageWorks) {
      try {
        window.localStorage.removeItem(STORAGE_KEY);
      } catch (_error) {
        storageWorks = false;
      }
    }
    state = createDefaultState();
    trustedSetupMessage = null;
    messageImportError = "";
    elements.resetDialog.close();
    render({ focusHeading: true });
    showToast("Launcher reset");
  });

  document.addEventListener("click", function (event) {
    const closeControl = event.target.closest("[data-close-dialog]");
    if (closeControl) {
      const dialog = document.getElementById(closeControl.dataset.closeDialog);
      if (dialog && typeof dialog.close === "function") {
        dialog.close();
      }
    }

    if (event.target.closest("#confirm-manual-help-copy")) {
      const recovery = document.getElementById("manual-copy-recovery");
      if (recovery) {
        recovery.hidden = true;
      }
      elements.helpError.textContent = "";
      elements.helpCopyStatus.hidden = false;
      elements.chatgptFallback.hidden = false;
      elements.chatgptFallback.focus();
    }
  });

  elements.chatgptFallback.addEventListener("click", function () {
    elements.helpDialog.close();
    elements.helpQuestion.value = "";
    elements.questionCount.textContent = "0 / 1200";
  });

  elements.helpQuestion.addEventListener("input", function () {
    const length = elements.helpQuestion.value.length;
    elements.questionCount.textContent = length + " / 1200";
    if (elements.helpQuestion.value.trim()) {
      elements.helpError.textContent = "";
      elements.helpQuestion.removeAttribute("aria-invalid");
    }
  });

  elements.helpForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    const question = elements.helpQuestion.value.trim();

    if (!question) {
      elements.helpQuestion.setAttribute("aria-invalid", "true");
      elements.helpError.textContent = "Type the setup question you want ChatGPT to help with.";
      elements.helpQuestion.focus();
      return;
    }

    const submitButton = elements.helpForm.querySelector('button[type="submit"]');
    const prompt = helpPrompt(question);
    submitButton.disabled = true;
    elements.helpError.textContent = "";
    const copied = await copyText(prompt);
    submitButton.disabled = false;

    if (!copied) {
      elements.helpError.textContent = "Automatic copy was blocked. Use the one copy action shown below.";
      showManualCopyRecovery(prompt);
      return;
    }

    elements.helpCopyStatus.hidden = false;
    elements.chatgptFallback.hidden = false;
    elements.chatgptFallback.focus();
    showToast("Help prompt copied");
  });

  async function initialize() {
    await loadReleaseMetadata();
    render();
  }

  elements.chatgptFallback.href = chatgptUrl;
  initialize();
})();
