(function () {
    "use strict";

    function escapeHtml(text) {
        var div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function userAvatarEl() {
        var ava = document.createElement("span");
        ava.className = "assistant-avatar is-user";
        ava.innerHTML = '<i class="bi bi-person-fill"></i>';
        return ava;
    }

    function botAvatarEl(src) {
        var ava = document.createElement("span");
        ava.className = "assistant-avatar is-bot";
        if (src) {
            var img = document.createElement("img");
            img.src = src;
            img.alt = "";
            ava.appendChild(img);
        } else {
            ava.innerHTML = '<i class="bi bi-robot-fill"></i>';
        }
        return ava;
    }

    function makeBubble(text, role, sources, botAvatar) {
        var row = document.createElement("div");
        row.className = "assistant-msg-row assistant-row-" + role;

        if (role === "user") {
            row.appendChild(userAvatarEl());
        } else if (role === "assistant") {
            row.appendChild(botAvatarEl(botAvatar));
        }

        var el = document.createElement("div");
        el.className = "assistant-msg " + role;

        var body = document.createElement("div");
        body.className = "assistant-msg-text";
        body.innerHTML = escapeHtml(text);
        el.appendChild(body);

        if (sources && sources.length) {
            var box = document.createElement("div");
            box.className = "assistant-msg-sources";
            var title = document.createElement("div");
            title.className = "assistant-msg-sources-title";
            var sourcesLabel = (window.__assistantStrings && window.__assistantStrings.sources) || "Sources";
            title.innerHTML = '<i class="bi bi-link-45deg"></i> ' + escapeHtml(sourcesLabel);
            box.appendChild(title);
            var ul = document.createElement("ul");
            sources.forEach(function (source) {
                var li = document.createElement("li");
                var a = document.createElement("a");
                a.href = source.url || "#";
                a.target = "_blank";
                a.rel = "noopener noreferrer";
                a.textContent = source.title || source.url || "Source";
                li.appendChild(a);
                ul.appendChild(li);
            });
            box.appendChild(ul);
            el.appendChild(box);
        }

        row.appendChild(el);
        return row;
    }

    function makeTypingBubble(botAvatar) {
        var row = document.createElement("div");
        row.className = "assistant-msg-row assistant-row-typing";
        row.appendChild(botAvatarEl(botAvatar));

        var el = document.createElement("div");
        el.className = "assistant-msg typing";
        for (var i = 0; i < 3; i++) {
            var dot = document.createElement("span");
            dot.className = "assistant-typing-dot";
            el.appendChild(dot);
        }
        row.appendChild(el);
        return row;
    }

    function scrollToBottom(el) {
        requestAnimationFrame(function () {
            el.scrollTop = el.scrollHeight;
        });
    }

    // ------------------------------------------------------------------
    // Auto-resize textarea
    // ------------------------------------------------------------------

    function autoResize(textarea) {
        textarea.style.height = "auto";
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + "px";
    }

    // ------------------------------------------------------------------
    // Character emotion controller
    // ------------------------------------------------------------------

    function CharacterController(root, imgSelector, defaultEmotion) {
        this.root = root;
        this.img = root.querySelector(imgSelector);
        this.defaultEmotion = defaultEmotion || "calm";
        this.current = this.defaultEmotion;

        var jsonEl = root.querySelector('script[type="application/json"]');
        this.emotions = {};
        if (jsonEl) {
            try {
                this.emotions = JSON.parse(jsonEl.textContent) || {};
            } catch (e) {
                this.emotions = {};
            }
        }

        this.setEmotion = function (emotion, animate) {
            if (!this.img) return;
            var key = this.emotions[emotion] ? emotion : this.defaultEmotion;
            if (this.emotions[key]) {
                this.img.src = this.emotions[key];
            }
            this.current = key;
            if (animate !== false) {
                this.img.classList.remove("assistant-emotion-bounce");
                void this.img.offsetWidth;
                this.img.classList.add("assistant-emotion-bounce");
            }
        };

        this.setThinking = function () {
            this.setEmotion("thinking", true);
        };
    }

    function initCharacter(root, imgSelector, defaultEmotion) {
        return new CharacterController(root, imgSelector, defaultEmotion);
    }

    // ------------------------------------------------------------------
    // Chat engine
    // ------------------------------------------------------------------

    function AssistantChat(options) {
        this.endpoint = options.endpoint;
        this.csrf = options.csrf;
        this.messagesEl = options.messagesEl;
        this.inputEl = options.inputEl;
        this.sendBtn = options.sendBtn;
        this.character = options.character || null;
        this.botAvatar = options.botAvatar || "";
        this.suggestionsEl = options.suggestionsEl || null;
        this.conversationId = null;
        this.busy = false;

        var self = this;

        function hideSuggestions() {
            if (self.suggestionsEl) {
                self.suggestionsEl.classList.remove("assistant-show");
                self.suggestionsEl.setAttribute("aria-hidden", "true");
            }
        }

        function showSuggestions() {
            if (self.suggestionsEl) {
                self.suggestionsEl.classList.add("assistant-show");
                self.suggestionsEl.setAttribute("aria-hidden", "false");
            }
        }

        function doSend() {
            if (self.busy) return;
            var text = (self.inputEl.value || "").trim();
            if (!text) return;
            self.busy = true;
            self.inputEl.value = "";
            if (self.inputEl.tagName === "TEXTAREA") {
                autoResize(self.inputEl);
            }
            hideSuggestions();
            self.append(text, "user");
            var typing = makeTypingBubble(self.botAvatar);
            self.messagesEl.appendChild(typing);
            scrollToBottom(self.messagesEl);
            if (self.character) self.character.setThinking();

            var body = { message: text };
            if (self.conversationId) {
                body.conversation_id = self.conversationId;
            }

            fetch(self.endpoint, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": self.csrf
                },
                credentials: "same-origin",
                body: JSON.stringify(body)
            })
                .then(function (response) {
                    if (!response.ok) throw new Error("request failed");
                    return response.json();
                })
                .then(function (data) {
                    typing.remove();
                    self.conversationId = data.conversation_id || self.conversationId;
                    self.append(data.reply || "", "assistant", data.sources);
                    if (self.character) {
                        self.character.setEmotion(data.emotion || "happy", true);
                    }
                })
                .catch(function () {
                    typing.remove();
                    var msg = "Network error. Please try again.";
                    if (window.__assistantErrors && window.__assistantErrors.network) {
                        msg = window.__assistantErrors.network;
                    }
                    self.append(msg, "assistant");
                    if (self.character) self.character.setEmotion("wonder", true);
                })
                .finally(function () {
                    self.busy = false;
                    if (self.inputEl) self.inputEl.focus();
                });
        }

        this.append = function (text, role, sources) {
            this.messagesEl.appendChild(makeBubble(text, role, sources, this.botAvatar));
            scrollToBottom(this.messagesEl);
        };

        this.hasMessages = function () {
            return !!this.messagesEl.querySelector(".assistant-msg-row");
        };

        this.showSuggestions = showSuggestions;

        if (this.sendBtn) {
            this.sendBtn.addEventListener("click", doSend);
        }
        if (this.inputEl) {
            this.inputEl.addEventListener("keydown", function (event) {
                if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    doSend();
                }
            });
            this.inputEl.addEventListener("input", function () {
                autoResize(self.inputEl);
            });
        }
    }

    // ------------------------------------------------------------------
    // Floating widget
    // ------------------------------------------------------------------

    var root = document.getElementById("assistant-root");
    if (root) {
        var launcher = document.getElementById("assistant-launcher");
        var panel = document.getElementById("assistant-panel");
        var closeBtn = document.getElementById("assistant-close");
        var messagesEl = document.getElementById("assistant-messages");
        var inputEl = document.getElementById("assistant-input");
        var sendBtn = document.getElementById("assistant-send");
        var hintEl = document.getElementById("assistant-hint");
        var suggestionsEl = document.getElementById("assistant-suggestions");
        var welcome = root.dataset.welcome || "";
        var defaultEmotion = root.dataset.defaultEmotion || "calm";

        var characterImg = document.querySelector("#assistant-character-img");
        var botAvatar = characterImg ? characterImg.src : "";

        var character = initCharacter(root, "#assistant-character-img", defaultEmotion);

        var chat = new AssistantChat({
            endpoint: root.dataset.endpoint,
            csrf: root.dataset.csrf,
            messagesEl: messagesEl,
            inputEl: inputEl,
            sendBtn: sendBtn,
            character: character,
            botAvatar: botAvatar,
            suggestionsEl: suggestionsEl
        });

        function open(prefill, sendNow) {
            panel.classList.add("assistant-open");
            hintEl.classList.remove("assistant-visible");
            launcher.classList.remove("assistant-pulse");
            if (!chat.hasMessages()) {
                chat.append(welcome, "assistant");
                character.setEmotion("happy", true);
                chat.showSuggestions();
            }
            if (prefill) {
                inputEl.value = prefill;
            }
            if (sendNow && prefill) {
                chat.sendBtn.click();
            } else if (inputEl) {
                inputEl.focus();
            }
        }

        function close() {
            panel.classList.remove("assistant-open");
        }

        launcher.addEventListener("click", function () {
            if (panel.classList.contains("assistant-open")) {
                close();
            } else {
                open();
            }
        });

        closeBtn.addEventListener("click", close);

        hintEl.addEventListener("click", function () {
            open(hintEl.dataset.question || "", false);
            hintEl.classList.remove("assistant-visible");
        });

        if (suggestionsEl) {
            suggestionsEl.addEventListener("click", function (event) {
                var chip = event.target.closest(".assistant-chip");
                if (!chip || !chip.dataset.q) return;
                window.AssistantApp.send(chip.dataset.q);
            });
        }

        window.AssistantApp = {
            open: open,
            close: close,
            send: function (text) {
                open(text, true);
            }
        };

        function showHint(text, question) {
            hintEl.textContent = text;
            hintEl.dataset.question = question || "";
            hintEl.classList.add("assistant-visible");
            launcher.classList.add("assistant-pulse");
            character.setEmotion("wonder", true);
        }

        var errorCode = window.assistantError;

        if (errorCode) {
            var hints = {
                "404": {
                    text: (window.__assistantErrors && window.__assistantErrors.page404) || "This page does not exist.",
                    question: "404"
                },
                "403": {
                    text: (window.__assistantErrors && window.__assistantErrors.page403) || "Access denied.",
                    question: "403"
                },
                "500": {
                    text: (window.__assistantErrors && window.__assistantErrors.page500) || "Something went wrong.",
                    question: "500"
                }
            };
            var hint = hints[errorCode];
            if (hint) showHint(hint.text, hint.question);
        } else if (
            document.querySelector(".alert-danger") ||
            document.querySelector(".errorlist") ||
            document.querySelector(".has-error")
        ) {
            showHint(
                window.__assistantErrors && window.__assistantErrors.form
                    ? window.__assistantErrors.form
                    : "There seems to be a form error. I can help you fix it.",
                "help me fix a form error"
            );
        }
    }

    // ------------------------------------------------------------------
    // Full chat page
    // ------------------------------------------------------------------

    var pageRoot = document.getElementById("assistant-chat-root");
    if (pageRoot) {
        var pageCharacterImg = document.querySelector("#assistant-chat-character-img");
        var pageBotAvatar = pageCharacterImg ? pageCharacterImg.src : "";

        var pageCharacter = initCharacter(
            pageRoot,
            "#assistant-chat-character-img",
            "calm"
        );
        var pageChat = new AssistantChat({
            endpoint: pageRoot.dataset.endpoint,
            csrf: pageRoot.dataset.csrf,
            messagesEl: document.getElementById("assistant-chat-messages"),
            inputEl: document.getElementById("assistant-chat-input"),
            sendBtn: document.getElementById("assistant-chat-send"),
            character: pageCharacter,
            botAvatar: pageBotAvatar
        });
        window.AssistantPage = pageChat;

        // ------------------------------------------------------------------
        // File upload / summarization / analysis / PDF report
        // ------------------------------------------------------------------

        var attachBtn = document.getElementById("assistant-attach-btn");
        var fileInput = document.getElementById("assistant-file-input");
        var attachBar = document.getElementById("assistant-attachments");
        var attachList = document.getElementById("assistant-attachments-list");
        var btnSummarize = document.getElementById("assistant-btn-summarize");
        var btnAnalyze = document.getElementById("assistant-btn-analyze");
        var btnReport = document.getElementById("assistant-btn-report");

        var uploadEndpoint = pageRoot.dataset.uploadEndpoint || "";
        var analyzeEndpoint = pageRoot.dataset.analyzeEndpoint || "";
        var reportEndpoint = pageRoot.dataset.reportEndpoint || "";

        var maxFiles = parseInt(pageRoot.dataset.maxFiles || "10", 10);
        var maxSizeMb = parseInt(pageRoot.dataset.maxSizeMb || "20", 10);
        var maxSizeBytes = maxSizeMb * 1024 * 1024;

        var selectedFiles = [];

        var kindIcon = {
            pdf: "bi-file-earmark-pdf",
            docx: "bi-file-earmark-word",
            xlsx: "bi-file-earmark-excel",
            text: "bi-file-earmark-text",
            image: "bi-file-earmark-image",
            other: "bi-file-earmark"
        };

        function fileIcon(kind) {
            return kindIcon[kind] || kindIcon.other;
        }

        function updateFileButtons() {
            var hasFiles = selectedFiles.length > 0;
            btnSummarize.disabled = !hasFiles;
            btnAnalyze.disabled = !hasFiles;
            btnReport.disabled = !hasFiles;
            if (attachBar) {
                attachBar.hidden = !hasFiles;
            }
        }

        function renderFiles() {
            if (!attachList) return;
            attachList.innerHTML = "";
            selectedFiles.forEach(function (file, index) {
                var chip = document.createElement("span");
                chip.className = "assistant-file-chip";
                chip.innerHTML =
                    '<i class="bi ' + fileIcon(file.kind) + '"></i>' +
                    '<span class="assistant-file-chip-name">' + escapeHtml(file.name) + '</span>' +
                    '<span class="assistant-file-chip-size">' + escapeHtml(file.size_human || "") + '</span>' +
                    '<button type="button" class="assistant-file-chip-remove" aria-label="Remove" data-index="' + index + '">' +
                    '<i class="bi bi-x-lg"></i></button>';
                attachList.appendChild(chip);
            });

            attachList.querySelectorAll(".assistant-file-chip-remove").forEach(function (btn) {
                btn.addEventListener("click", function () {
                    var index = parseInt(btn.dataset.index, 10);
                    if (!isNaN(index)) {
                        selectedFiles.splice(index, 1);
                        renderFiles();
                        updateFileButtons();
                    }
                });
            });

            updateFileButtons();
        }

        function uploadFiles(fileList) {
            if (!fileList || !fileList.length || !uploadEndpoint) return;

            var formData = new FormData();
            var accepted = [];
            var skipped = [];

            Array.prototype.forEach.call(fileList, function (file) {
                if (accepted.length + selectedFiles.length >= maxFiles) {
                    skipped.push(file.name);
                    return;
                }
                if (file.size > maxSizeBytes) {
                    skipped.push(file.name + " (" + maxSizeMb + "MB)");
                    return;
                }
                accepted.push(file);
            });

            accepted.forEach(function (file) {
                formData.append("files", file);
            });

            if (!accepted.length) {
                if (skipped.length) {
                    var msg = (window.__assistantStrings && window.__assistantStrings.uploadError) ||
                        "Upload failed for: " + skipped.join(", ");
                    pageChat.append(msg, "assistant");
                }
                if (fileInput) fileInput.value = "";
                return;
            }

            btnSummarize.disabled = true;
            btnAnalyze.disabled = true;
            if (pageCharacter) pageCharacter.setThinking();

            fetch(uploadEndpoint, {
                method: "POST",
                headers: { "X-CSRFToken": pageRoot.dataset.csrf },
                credentials: "same-origin",
                body: formData
            })
                .then(function (response) {
                    return response.json().then(function (data) {
                        return { ok: response.ok, data: data };
                    });
                })
                .then(function (result) {
                    var data = result.data || {};
                    if (data.files) {
                        data.files.forEach(function (item) { selectedFiles.push(item); });
                    }
                    if (data.errors && data.errors.length) {
                        var errorNames = data.errors.map(function (err) { return err.name; }).join(", ");
                        pageChat.append(
                            ((window.__assistantStrings && window.__assistantStrings.uploadError) || "Upload failed.") +
                            " " + errorNames,
                            "assistant"
                        );
                    }
                    renderFiles();
                    if (data.files && data.files.length) {
                        pageChat.append(
                            (window.__assistantStrings && window.__assistantStrings.summarize) || "Files uploaded.",
                            "user"
                        );
                    }
                    if (pageCharacter) pageCharacter.setEmotion("happy", true);
                })
                .catch(function () {
                    var msg = (window.__assistantStrings && window.__assistantStrings.uploadError) ||
                        "Upload failed. Please try again.";
                    pageChat.append(msg, "assistant");
                    if (pageCharacter) pageCharacter.setEmotion("wonder", true);
                })
                .finally(function () {
                    if (fileInput) fileInput.value = "";
                    updateFileButtons();
                });
        }

        function runAnalysis(task, question) {
            if (!selectedFiles.length || !analyzeEndpoint) return;

            var body = {
                attachment_ids: selectedFiles.map(function (f) { return f.id; }),
                task: task
            };
            if (question) body.question = question;

            btnSummarize.disabled = true;
            btnAnalyze.disabled = true;
            if (pageCharacter) pageCharacter.setThinking();

            var typing = makeTypingBubble(pageBotAvatar);
            pageChat.messagesEl.appendChild(typing);
            scrollToBottom(pageChat.messagesEl);

            fetch(analyzeEndpoint, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": pageRoot.dataset.csrf
                },
                credentials: "same-origin",
                body: JSON.stringify(body)
            })
                .then(function (response) {
                    if (!response.ok) throw new Error("request failed");
                    return response.json();
                })
                .then(function (data) {
                    typing.remove();
                    pageChat.conversationId = data.conversation_id || pageChat.conversationId;
                    pageChat.append(data.reply || "", "assistant", data.sources);
                    if (pageCharacter) pageCharacter.setEmotion(data.emotion || "happy", true);
                })
                .catch(function () {
                    typing.remove();
                    var msg = (window.__assistantStrings && window.__assistantStrings.analyzeError) ||
                        "Analysis failed. Please try again.";
                    pageChat.append(msg, "assistant");
                    if (pageCharacter) pageCharacter.setEmotion("wonder", true);
                })
                .finally(function () {
                    updateFileButtons();
                });
        }

        function generateReport() {
            if (!selectedFiles.length || !reportEndpoint) return;

            if (pageCharacter) pageCharacter.setThinking();
            btnReport.disabled = true;

            var lastAssistant = pageChat.messagesEl.querySelector(
                ".assistant-msg-row.assistant-row-assistant .assistant-msg-text"
            );
            var notes = lastAssistant ? lastAssistant.textContent : "";

            fetch(reportEndpoint, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": pageRoot.dataset.csrf
                },
                credentials: "same-origin",
                body: JSON.stringify({
                    attachment_ids: selectedFiles.map(function (f) { return f.id; }),
                    notes: notes
                })
            })
                .then(function (response) {
                    if (!response.ok) throw new Error("request failed");
                    return response.blob();
                })
                .then(function (blob) {
                    var url = URL.createObjectURL(blob);
                    var link = document.createElement("a");
                    link.href = url;
                    link.download = "assistant-report.pdf";
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    URL.revokeObjectURL(url);
                    if (pageCharacter) pageCharacter.setEmotion("happy", true);
                })
                .catch(function () {
                    var msg = (window.__assistantStrings && window.__assistantStrings.analyzeError) ||
                        "Report generation failed.";
                    pageChat.append(msg, "assistant");
                    if (pageCharacter) pageCharacter.setEmotion("wonder", true);
                })
                .finally(function () {
                    updateFileButtons();
                });
        }

        if (attachBtn) {
            attachBtn.addEventListener("click", function () {
                if (fileInput) fileInput.click();
            });
        }

        if (fileInput) {
            fileInput.addEventListener("change", function () {
                uploadFiles(fileInput.files);
            });
        }

        if (btnSummarize) {
            btnSummarize.addEventListener("click", function () {
                runAnalysis("summarize", "");
            });
        }

        if (btnAnalyze) {
            btnAnalyze.addEventListener("click", function () {
                runAnalysis("analyze", "");
            });
        }

        if (btnReport) {
            btnReport.addEventListener("click", generateReport);
        }

        function doChatWithFiles(body) {
            if (pageChat.busy) return;
            pageChat.busy = true;
            var text = body.message;
            pageChat.inputEl.value = "";
            if (pageChat.inputEl.tagName === "TEXTAREA") {
                autoResize(pageChat.inputEl);
            }
            pageChat.append(text, "user");
            var typing = makeTypingBubble(pageBotAvatar);
            pageChat.messagesEl.appendChild(typing);
            scrollToBottom(pageChat.messagesEl);
            if (pageCharacter) pageCharacter.setThinking();

            fetch(pageChat.endpoint, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": pageChat.csrf
                },
                credentials: "same-origin",
                body: JSON.stringify(body)
            })
                .then(function (response) {
                    if (!response.ok) throw new Error("request failed");
                    return response.json();
                })
                .then(function (data) {
                    typing.remove();
                    pageChat.conversationId = data.conversation_id || pageChat.conversationId;
                    pageChat.append(data.reply || "", "assistant", data.sources);
                    if (pageCharacter) pageCharacter.setEmotion(data.emotion || "happy", true);
                })
                .catch(function () {
                    typing.remove();
                    var msg = (window.__assistantStrings && window.__assistantStrings.analyzeError) ||
                        "Network error. Please try again.";
                    pageChat.append(msg, "assistant");
                    if (pageCharacter) pageCharacter.setEmotion("wonder", true);
                })
                .finally(function () {
                    pageChat.busy = false;
                    if (pageChat.inputEl) pageChat.inputEl.focus();
                });
        }

        if (pageChat.sendBtn) {
            pageChat.sendBtn.addEventListener("click", function () {
                var text = (pageChat.inputEl && pageChat.inputEl.value || "").trim();
                if (selectedFiles.length && text) {
                    var body = {
                        message: text,
                        attachment_ids: selectedFiles.map(function (f) { return f.id; })
                    };
                    if (pageChat.conversationId) body.conversation_id = pageChat.conversationId;
                    doChatWithFiles(body);
                }
            });
        }

        if (pageChat.inputEl) {
            pageChat.inputEl.addEventListener("keydown", function (event) {
                if (event.key === "Enter" && !event.shiftKey) {
                    var text = (pageChat.inputEl.value || "").trim();
                    if (selectedFiles.length && text) {
                        event.preventDefault();
                        var body = {
                            message: text,
                            attachment_ids: selectedFiles.map(function (f) { return f.id; })
                        };
                        if (pageChat.conversationId) body.conversation_id = pageChat.conversationId;
                        doChatWithFiles(body);
                    }
                }
            });
        }

        updateFileButtons();

        // ------------------------------------------------------------------
        // Sidebar toggle
        // ------------------------------------------------------------------

        var sidebarToggle = document.getElementById("assistant-sidebar-toggle");
        var sidebar = document.getElementById("assistant-sidebar");
        var sidebarBackdrop = document.getElementById("assistant-sidebar-backdrop");
        var sidebarClose = document.getElementById("assistant-sidebar-close");

        function openSidebar() {
            if (!sidebar) return;
            sidebar.classList.add("assistant-sidebar-open");
            sidebar.classList.remove("assistant-sidebar-collapsed");
            if (sidebarBackdrop) sidebarBackdrop.classList.add("active");
        }

        function closeSidebar() {
            if (!sidebar) return;
            sidebar.classList.remove("assistant-sidebar-open");
            sidebar.classList.add("assistant-sidebar-collapsed");
            if (sidebarBackdrop) sidebarBackdrop.classList.remove("active");
        }

        if (sidebarToggle && sidebar) {
            sidebarToggle.addEventListener("click", function () {
                if (sidebar.classList.contains("assistant-sidebar-open")) {
                    closeSidebar();
                } else {
                    openSidebar();
                }
            });
        }

        if (sidebarClose) {
            sidebarClose.addEventListener("click", closeSidebar);
        }

        if (sidebarBackdrop) {
            sidebarBackdrop.addEventListener("click", closeSidebar);
        }

        // ------------------------------------------------------------------
        // New chat button
        // ------------------------------------------------------------------

        var newChatBtn = document.getElementById("assistant-new-chat-btn");
        if (newChatBtn) {
            newChatBtn.addEventListener("click", function () {
                pageChat.conversationId = null;
                pageChat.messagesEl.innerHTML = "";
                if (pageCharacter) pageCharacter.setEmotion("happy", true);
                closeSidebar();
                if (pageChat.inputEl) pageChat.inputEl.focus();
            });
        }

        // ------------------------------------------------------------------
        // Drag-and-drop file upload
        // ------------------------------------------------------------------

        var dropZone = document.getElementById("assistant-drop-zone");
        var chatCard = pageRoot.querySelector(".assistant-chat-card");
        var dragCounter = 0;

        if (chatCard && dropZone) {
            chatCard.addEventListener("dragenter", function (e) {
                e.preventDefault();
                dragCounter++;
                dropZone.hidden = false;
            });

            chatCard.addEventListener("dragleave", function (e) {
                e.preventDefault();
                dragCounter--;
                if (dragCounter <= 0) {
                    dragCounter = 0;
                    dropZone.hidden = true;
                }
            });

            chatCard.addEventListener("dragover", function (e) {
                e.preventDefault();
            });

            chatCard.addEventListener("drop", function (e) {
                e.preventDefault();
                dragCounter = 0;
                dropZone.hidden = true;
                if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
                    uploadFiles(e.dataTransfer.files);
                }
            });
        }

        // ------------------------------------------------------------------
        // Empty-state suggestion chips
        // ------------------------------------------------------------------

        var messagesEl = document.getElementById("assistant-chat-messages");
        if (messagesEl) {
            messagesEl.addEventListener("click", function (e) {
                var chip = e.target.closest(".assistant-empty-chips .assistant-chip");
                if (!chip || !chip.dataset.q) return;
                pageChat.inputEl.value = chip.dataset.q;
                pageChat.sendBtn.click();
            });
        }
    }
})();
