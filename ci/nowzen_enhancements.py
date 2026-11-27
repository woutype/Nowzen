#!/usr/bin/env python3
"""Post-patch Nowzen UX, stability, privacy, and feature enhancements."""
from pathlib import Path


def _replace_once(path: Path, old: str, new: str, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Missing target file for {label}: {path}")
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise ValueError(f"Anchor not found for {label} in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _enhance_app_delegate(src: Path) -> None:
    path = src / "submodules/TelegramUI/Sources/AppDelegate.swift"

    # 1. Remove grey/blur overlay when minimizing/switching apps.
    _replace_once(
        path,
        """    private func ayuUpdateSwitcherBlur(active: Bool) {
        if active, AyuExtras.isOn(.blurInAppSwitcher), self.ayuSwitcherBlurView == nil, let window = self.window {
            let blur = UIVisualEffectView(effect: UIBlurEffect(style: .systemThickMaterial))
            blur.frame = window.bounds
            blur.autoresizingMask = [.flexibleWidth, .flexibleHeight]
            window.addSubview(blur)
            self.ayuSwitcherBlurView = blur
        } else if !active, let blur = self.ayuSwitcherBlurView {""",
        """    private func ayuUpdateSwitcherBlur(active: Bool) {
        if active {
            return
        } else if !active, let blur = self.ayuSwitcherBlurView {""",
        "disable_switcher_blur",
    )

    # 2. Register Home Screen Quick Action "Войти в Ghost Mode" and handle it before going online.
    _replace_once(
        path,
        """    func handleDidBecomeActive() {
        self.ayuUpdateSwitcherBlur(active: false)
        AyuVerifiedRegistry.shared.refresh()""",
        """    func ayuUpdateQuickActions() {
        if AyuDecoyMode.isActive {
            UIApplication.shared.shortcutItems = []
            return
        }
        let ru = Locale.preferredLanguages.first?.hasPrefix("ru") == true
        let ghostShortcut = UIApplicationShortcutItem(
            type: "com.nowzen.enterGhostMode",
            localizedTitle: ru ? "Войти в Ghost Mode" : "Enter Ghost Mode",
            localizedSubtitle: ru ? "Открыть без статуса «в сети»" : "Open without going online",
            icon: UIApplicationShortcutIcon(systemImageName: "eye.slash.fill"),
            userInfo: nil
        )
        var current = UIApplication.shared.shortcutItems ?? []
        current.removeAll { $0.type == "com.nowzen.enterGhostMode" }
        current.insert(ghostShortcut, at: 0)
        UIApplication.shared.shortcutItems = current
    }

    func ayuEnableGhostModeForLaunch() {
        UserDefaults.standard.set(true, forKey: "ayu.launch.forceGhostMode")
        guard let sharedContext = self.sharedContext else { return }
        let _ = (sharedContext.activeAccountContexts |> take(1) |> deliverOnMainQueue).startStandalone(next: { primary, contexts, _ in
            var targets = contexts.map { $0.1 }
            if let primary, !targets.contains(where: { $0.account.id == primary.account.id }) {
                targets.append(primary)
            }
            for ctx in targets {
                try? ctx.account.network.ayuGhostMode.update { settings in
                    settings.hideReadReceipts = true
                    settings.hideOnline = true
                    settings.hideTyping = true
                    settings.hideUploadProgress = true
                }
            }
        })
    }

    func application(_ application: UIApplication, performActionFor shortcutItem: UIApplicationShortcutItem, completionHandler: @escaping (Bool) -> Void) {
        if shortcutItem.type == "com.nowzen.enterGhostMode" {
            self.ayuEnableGhostModeForLaunch()
            completionHandler(true)
            return
        }
        completionHandler(false)
    }

    func handleDidBecomeActive() {
        self.ayuUpdateSwitcherBlur(active: false)
        self.ayuUpdateQuickActions()
        AyuVerifiedRegistry.shared.refresh()""",
        "quick_action_ghost_mode",
    )


def _enhance_app_extras_defaults(src: Path) -> None:
    path = src / "submodules/TelegramUI/Sources/AyuAppExtras.swift"
    _replace_once(
        path,
        """                if preset == 0 {
                    for key in [AyuExtras.Key.spoofPhotoMetadata, .randomFileNames, .cleanLinks, .blurInAppSwitcher] {
                        AyuExtras.set(key, true)
                    }
                }""",
        """                if preset == 0 {
                    for key in [AyuExtras.Key.spoofPhotoMetadata, .randomFileNames, .cleanLinks, .saveViewOnce, .viewOnceReview] {
                        AyuExtras.set(key, true)
                    }
                }
                AyuExtras.set(.blurInAppSwitcher, false)""",
        "preset_defaults_no_blur_and_viewonce",
    )


def _enhance_chat_privacy_and_face_id(src: Path) -> None:
    # 1. Add centralized Face ID authentication helper to AyuChatPrivacy
    privacy_path = src / "submodules/Display/Source/AyuChatPrivacy.swift"
    _replace_once(
        privacy_path,
        "import Foundation\n",
        "import Foundation\nimport LocalAuthentication\n",
        "chat_privacy_import_la",
    )
    _replace_once(
        privacy_path,
        """    public static func isUnlocked(_ peerId: Int64) -> Bool {
        lock.lock(); defer { lock.unlock() }
        return unlocked.contains(peerId)
    }""",
        """    public static func authenticate(reason: String, completion: @escaping (Bool) -> Void) {
        let context = LAContext()
        var error: NSError?
        guard context.canEvaluatePolicy(.deviceOwnerAuthentication, error: &error) else {
            DispatchQueue.main.async { completion(true) }
            return
        }
        context.evaluatePolicy(.deviceOwnerAuthentication, localizedReason: reason) { success, _ in
            DispatchQueue.main.async {
                completion(success)
            }
        }
    }

    public static func isUnlocked(_ peerId: Int64) -> Bool {
        lock.lock(); defer { lock.unlock() }
        return unlocked.contains(peerId)
    }""",
        "chat_privacy_authenticate_helper",
    )

    # 2. Require Face ID before removing Face ID lock in ChatList context menu
    menus_path = src / "submodules/ChatListUI/Sources/ChatContextMenus.swift"
    _replace_once(
        menus_path,
        """                            items.append(.action(ContextMenuActionItem(text: ayuLocked ? (ayuRu ? "Снять блокировку Face ID" : "Remove Face ID lock") : (ayuRu ? "Заблокировать Face ID" : "Lock with Face ID"), icon: { theme in UIImage(systemName: ayuLocked ? "lock.open.fill" : "faceid")?.withTintColor(theme.contextMenu.primaryColor, renderingMode: .alwaysOriginal) }, action: { _, f in
                                AyuChatPrivacy.setLocked(ayuPeerValue, !ayuLocked)
                                f(.default)
                            })))""",
        """                            items.append(.action(ContextMenuActionItem(text: ayuLocked ? (ayuRu ? "Снять блокировку Face ID" : "Remove Face ID lock") : (ayuRu ? "Заблокировать Face ID" : "Lock with Face ID"), icon: { theme in UIImage(systemName: ayuLocked ? "lock.open.fill" : "faceid")?.withTintColor(theme.contextMenu.primaryColor, renderingMode: .alwaysOriginal) }, action: { _, f in
                                if ayuLocked {
                                    f(.default)
                                    let reason = ayuRu ? "Подтвердите Face ID, чтобы снять блокировку чата" : "Authenticate to remove Face ID lock"
                                    AyuChatPrivacy.authenticate(reason: reason) { success in
                                        if success {
                                            AyuChatPrivacy.setLocked(ayuPeerValue, false)
                                        }
                                    }
                                } else {
                                    AyuChatPrivacy.setLocked(ayuPeerValue, true)
                                    f(.default)
                                }
                            })))""",
        "require_faceid_before_unlock",
    )

    # 3. Fix ChatLockView freezing, stray taps behind overlay, and duplicate auth calls
    lock_path = src / "submodules/TelegramUI/Sources/AyuChatLock.swift"
    _replace_once(
        lock_path,
        """extension ChatControllerImpl {
    /// Covers a locked chat and asks for Face ID / Touch ID (or the device passcode).
    func ayuApplyChatLock() {
        guard let peerId = self.chatLocation.peerId else { return }
        let value = peerId.toInt64()
        guard AyuChatPrivacy.isLocked(value), !AyuChatPrivacy.isUnlocked(value) else { return }
        if self.view.subviews.contains(where: { $0 is AyuChatLockView }) {
            return
        }
        let lockView = AyuChatLockView(frame: self.view.bounds)
        lockView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        self.view.addSubview(lockView)
        let authenticate = { [weak self, weak lockView] in
            let context = LAContext()
            let ru = Locale.preferredLanguages.first?.hasPrefix("ru") == true
            var error: NSError?
            guard context.canEvaluatePolicy(.deviceOwnerAuthentication, error: &error) else {
                // No Face ID and no passcode on the device: nothing to check against.
                AyuChatPrivacy.markUnlocked(value)
                lockView?.removeFromSuperview()
                return
            }
            context.evaluatePolicy(.deviceOwnerAuthentication, localizedReason: ru ? "Откройте заблокированный чат" : "Open the locked chat", reply: { success, _ in
                DispatchQueue.main.async {
                    if success {
                        AyuChatPrivacy.markUnlocked(value)
                        UIView.animate(withDuration: 0.2, animations: { lockView?.alpha = 0.0 }, completion: { _ in lockView?.removeFromSuperview() })
                    } else if let self {
                        let _ = self.navigationController?.popViewController(animated: true)
                    }
                }
            })
        }
        lockView.unlock = authenticate
        DispatchQueue.main.async {
            authenticate()
        }
    }
}""",
        """private var ayuChatLockAuthenticatingKey: UInt8 = 0

extension ChatControllerImpl {
    private var ayuIsAuthenticatingLock: Bool {
        get { (objc_getAssociatedObject(self, &ayuChatLockAuthenticatingKey) as? Bool) ?? false }
        set { objc_setAssociatedObject(self, &ayuChatLockAuthenticatingKey, newValue, .OBJC_ASSOCIATION_RETAIN_NONATOMIC) }
    }

    /// Covers a locked chat and asks for Face ID / Touch ID (or the device passcode).
    func ayuApplyChatLock() {
        guard let peerId = self.chatLocation.peerId else { return }
        let value = peerId.toInt64()
        guard AyuChatPrivacy.isLocked(value), !AyuChatPrivacy.isUnlocked(value) else { return }
        if self.view.subviews.contains(where: { $0 is AyuChatLockView }) {
            return
        }
        let lockView = AyuChatLockView(frame: self.view.bounds)
        lockView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        lockView.isUserInteractionEnabled = true
        lockView.isExclusiveTouch = true
        self.view.addSubview(lockView)
        self.view.bringSubviewToFront(lockView)
        let authenticate = { [weak self, weak lockView] in
            guard let self, !self.ayuIsAuthenticatingLock else { return }
            self.ayuIsAuthenticatingLock = true
            let context = LAContext()
            let ru = Locale.preferredLanguages.first?.hasPrefix("ru") == true
            var error: NSError?
            guard context.canEvaluatePolicy(.deviceOwnerAuthentication, error: &error) else {
                self.ayuIsAuthenticatingLock = false
                AyuChatPrivacy.markUnlocked(value)
                lockView?.removeFromSuperview()
                return
            }
            context.evaluatePolicy(.deviceOwnerAuthentication, localizedReason: ru ? "Откройте заблокированный чат" : "Open the locked chat", reply: { success, _ in
                DispatchQueue.main.async {
                    self.ayuIsAuthenticatingLock = false
                    if success {
                        AyuChatPrivacy.markUnlocked(value)
                        UIView.animate(withDuration: 0.2, animations: { lockView?.alpha = 0.0 }, completion: { _ in lockView?.removeFromSuperview() })
                    } else {
                        let _ = self.navigationController?.popViewController(animated: true)
                    }
                }
            })
        }
        lockView.unlock = authenticate
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) {
            authenticate()
        }
    }
}""",
        "fix_chat_lock_interaction_and_hang",
    )


def _enhance_ghost_mode_and_stories(src: Path) -> None:
    # 1. Disable per-chat ghost button by default (replaced by global chat-list button)
    settings_path = src / "submodules/TelegramCore/Sources/AyuGram/AyuGhostModeSettings.swift"
    _replace_once(
        settings_path,
        "    public var showGhostButton = true",
        "    public var showGhostButton = false",
        "default_hide_per_chat_ghost_button",
    )

    # 2. Tie anonymous story viewing explicitly to Ghost Mode
    story_path = src / "submodules/TelegramCore/Sources/AyuGram/AyuStoryPrivacy.swift"
    if story_path.is_file():
        _replace_once(
            story_path,
            """    public static var isEnabled: Bool {
        get { return UserDefaults.standard.bool(forKey: key) }
        set { UserDefaults.standard.set(newValue, forKey: key) }
    }

    public static func hidesViews(_ network: Network) -> Bool {
        return isEnabled && !AyuDecoyState.isActive && network.ayuGhostMode.current.hideReadReceipts
    }""",
            """    public static var isEnabled: Bool {
        get { return UserDefaults.standard.object(forKey: key) as? Bool ?? true }
        set { UserDefaults.standard.set(newValue, forKey: key) }
    }

    public static func hidesViews(_ network: Network) -> Bool {
        return isEnabled && !AyuDecoyState.isActive && network.ayuGhostMode.current.isActive
    }""",
            "explicit_story_privacy_with_ghost_mode",
        )

    # 3. Add global Ghost Mode floating toggle button in ChatListController
    cl_path = src / "submodules/ChatListUI/Sources/ChatListController.swift"
    _replace_once(
        cl_path,
        """    private var ayuComposeButton: UIButton?
    private var ayuSearchActive = false""",
        """    private var ayuComposeButton: UIButton?
    private var ayuGhostListButton: UIButton?
    private var ayuSearchActive = false""",
        "chatlist_ghost_button_property",
    )
    _replace_once(
        cl_path,
        "        self.updateAyuComposeButton(layout: layout, transition: transition)",
        "        self.updateAyuComposeButton(layout: layout, transition: transition)\n        self.updateAyuGhostListButton(layout: layout, transition: transition)",
        "chatlist_ghost_button_layout_call",
    )
    _replace_once(
        cl_path,
        """    private func updateAyuComposeButton(layout: ContainerViewLayout, transition: ContainedViewLayoutTransition) {""",
        """    private func updateAyuGhostListButton(layout: ContainerViewLayout, transition: ContainedViewLayoutTransition) {
        guard case .chatList(.root) = self.location, !AyuDecoyMode.isActive else {
            self.ayuGhostListButton?.isHidden = true
            return
        }
        let button: UIButton
        if let current = self.ayuGhostListButton {
            button = current
        } else {
            button = UIButton(type: .system)
            button.layer.cornerRadius = 22.0
            button.layer.cornerCurve = .continuous
            button.layer.shadowColor = UIColor.black.cgColor
            button.layer.shadowOpacity = 0.16
            button.layer.shadowRadius = 6.0
            button.layer.shadowOffset = CGSize(width: 0.0, height: 3.0)
            button.addTarget(self, action: #selector(self.ayuGhostListButtonPressed), for: .touchUpInside)
            self.chatListDisplayNode.view.addSubview(button)
            self.ayuGhostListButton = button
        }
        let active = self.context.account.network.ayuGhostMode.current.isActive
        let iconName = active ? "eye.slash.fill" : "eye.fill"
        button.setImage(UIImage(systemName: iconName, withConfiguration: UIImage.SymbolConfiguration(pointSize: 18.0, weight: .semibold)), for: .normal)
        button.backgroundColor = active ? self.presentationData.theme.list.itemAccentColor : self.presentationData.theme.list.itemBlocksBackgroundColor
        button.tintColor = active ? self.presentationData.theme.list.itemCheckColors.foregroundColor : self.presentationData.theme.list.itemPrimaryTextColor
        button.isHidden = self.ayuSearchActive || self.chatListDisplayNode.searchDisplayController != nil || self.chatListDisplayNode.isEditing || (layout.inputHeight ?? 0.0) > 0.0
        let size: CGFloat = 44.0
        let bottomOffset: CGFloat = (self.ayuComposeButton?.isHidden == false) ? 74.0 : 16.0
        let frame = CGRect(
            x: layout.size.width - layout.safeInsets.right - size - 16.0,
            y: layout.size.height - layout.intrinsicInsets.bottom - size - bottomOffset,
            width: size,
            height: size
        )
        transition.updateFrame(view: button, frame: frame)
    }

    @objc private func ayuGhostListButtonPressed() {
        let currentActive = self.context.account.network.ayuGhostMode.current.isActive
        let enable = !currentActive
        try? self.context.account.network.ayuGhostMode.update { settings in
            settings.hideReadReceipts = enable
            settings.hideOnline = enable
            settings.hideTyping = enable
            settings.hideUploadProgress = enable
        }
        if let layout = self.validLayout {
            self.updateAyuGhostListButton(layout: layout, transition: .animated(duration: 0.2, curve: .easeInOut))
        }
    }

    private func updateAyuComposeButton(layout: ContainerViewLayout, transition: ContainedViewLayoutTransition) {""",
        "chatlist_ghost_button_impl",
    )


def _enhance_deleted_and_view_once_media(src: Path) -> None:
    history_path = src / "submodules/TelegramCore/Sources/AyuGram/AyuMessageHistory.swift"

    # 1. Support all common media types (video notes, voice, stickers, photos, videos, files, contacts, locations)
    _replace_once(
        history_path,
        """private func ayuHistorySupportedMedia(_ media: [Media]) -> Bool {
    return media.allSatisfy { $0 is TelegramMediaWebpage || $0 is TelegramMediaImage || $0 is TelegramMediaFile }
}""",
        """private func ayuHistorySupportedMedia(_ media: [Media]) -> Bool {
    return media.allSatisfy {
        $0 is TelegramMediaWebpage || $0 is TelegramMediaImage || $0 is TelegramMediaFile || $0 is TelegramMediaMap || $0 is TelegramMediaContact
    }
}""",
        "history_support_all_media",
    )

    # 2. Allow archiving expiring/ephemeral messages (round videos, voice, view-once, auto-delete)
    _replace_once(
        history_path,
        """    if !peerAllows {
        state.remove(peerId: message.id.peerId.toInt64())
    } else if message.id.namespace != Namespaces.Message.Cloud || message.isCopyProtected() || ayuHistoryHasExpiringAttribute(message.attributes) || !updateAllows {""",
        """    if !peerAllows {
        state.remove(peerId: message.id.peerId.toInt64())
    } else if message.id.namespace != Namespaces.Message.Cloud || message.isCopyProtected() {""",
        "allow_archiving_expiring_media",
    )

    # 3. Retain original media (video notes, voice, photos, videos) in deleted tombstones instead of replacing with 📎/📷!
    _replace_once(
        history_path,
        """        var attributes = previous.attributes.filter {
            !($0 is AyuDeletedMessageAttribute) && !($0 is ReplyMarkupMessageAttribute) && !($0 is ReactionsMessageAttribute)
        }
        if state.saveReactions, let reactions = previous.reactionsAttribute { attributes.append(reactions) }
        attributes.append(AyuDeletedMessageAttribute(timestamp: Int64(Date().timeIntervalSince1970)))
        var flags = StoreMessageFlags(previous.flags)
        flags.remove(.TopIndexable)
        flags.remove(.CountedAsIncoming)
        flags.remove(.ReactionsArePossible)
        let tombstoneText = previous.text.isEmpty ? (previous.media.first is TelegramMediaImage ? "📷" : (previous.media.first is TelegramMediaFile ? "📎" : "💬")) : previous.text
        return .update(StoreMessage(id: previous.id, customStableId: nil, globallyUniqueId: previous.globallyUniqueId, groupingKey: nil, threadId: previous.threadId, timestamp: previous.timestamp, flags: flags, tags: [], globalTags: [], localTags: [], forwardInfo: forwardInfo, authorId: previous.author?.id, text: tombstoneText, attributes: attributes, media: []))""",
        """        var attributes = previous.attributes.filter {
            !($0 is AyuDeletedMessageAttribute) && !($0 is ReplyMarkupMessageAttribute) && !($0 is ReactionsMessageAttribute) && !($0 is AutoremoveTimeoutMessageAttribute) && !($0 is AutoclearTimeoutMessageAttribute) && !($0 is EphemeralMessageAttribute) && !($0 is EphemeralReplacementMessageAttribute)
        }
        if state.saveReactions, let reactions = previous.reactionsAttribute { attributes.append(reactions) }
        attributes.append(AyuDeletedMessageAttribute(timestamp: Int64(Date().timeIntervalSince1970)))
        var flags = StoreMessageFlags(previous.flags)
        flags.remove(.TopIndexable)
        flags.remove(.CountedAsIncoming)
        flags.remove(.ReactionsArePossible)
        let preservedMedia = previous.media
        let tombstoneText = (previous.text.isEmpty && preservedMedia.isEmpty) ? "💬" : previous.text
        return .update(StoreMessage(id: previous.id, customStableId: nil, globallyUniqueId: previous.globallyUniqueId, groupingKey: previous.groupingKey, threadId: previous.threadId, timestamp: previous.timestamp, flags: flags, tags: [], globalTags: [], localTags: [], forwardInfo: forwardInfo, authorId: previous.author?.id, text: tombstoneText, attributes: attributes, media: preservedMedia))""",
        "retain_media_in_deleted_tombstones",
    )

    # 4. In SecretMediaPreviewController: don't burn view-once media if Ghost Mode is active or saveViewOnce+viewOnceReview is enabled
    secret_preview_path = src / "submodules/GalleryUI/Sources/SecretMediaPreviewController.swift"
    _replace_once(
        secret_preview_path,
        """                // VoidGram "View again": opening view-once media does not count as viewing it.
                if !(AyuExtras.isOn(.saveViewOnce) && AyuExtras.isOn(.viewOnceReview)) {
                    self.markMessageAsConsumedDisposable.set(self.context.engine.messages.markMessageContentAsConsumedInteractively(messageId: message.id).start())
                }""",
        """                // Nowzen: keep view-once media unconsumed when Ghost Mode or view-once review is active.
                if !self.context.account.network.ayuGhostMode.current.isActive && !(AyuExtras.isOn(.saveViewOnce) && AyuExtras.isOn(.viewOnceReview)) {
                    self.markMessageAsConsumedDisposable.set(self.context.engine.messages.markMessageContentAsConsumedInteractively(messageId: message.id).start())
                }""",
        "view_once_ghost_auto_keep",
    )


def _enhance_history_notifications_and_context_menu(src: Path) -> None:
    # 1. Show old -> new text in edit notifications
    notif_path = src / "submodules/TelegramUI/Sources/AyuHistoryNotifications.swift"
    _replace_once(
        notif_path,
        """        let label = kind == "deleted" ? (ru ? "Сообщение удалено" : "Message deleted") : (ru ? "Сообщение изменено" : "Message edited")
        let content = UNMutableNotificationContent()
        content.title = visible ? peer.debugDisplayTitle + " · " + label : "VoidGram"
        content.body = visible ? (original.isEmpty ? (ru ? "Медиа" : "Media") : String(original.prefix(300))) : label""",
        """        let newText = info["newText"] as? String ?? ""
        let label = kind == "deleted" ? (ru ? "Сообщение удалено" : "Message deleted") : (ru ? "Сообщение изменено" : "Message edited")
        let content = UNMutableNotificationContent()
        content.title = visible ? peer.debugDisplayTitle + " · " + label : "Nowzen"
        if visible {
            if kind == "edited", !newText.isEmpty, newText != original {
                let fromText = original.isEmpty ? (ru ? "Медиа" : "Media") : String(original.prefix(130))
                let toText = String(newText.prefix(130))
                content.body = ru ? "Было: \\(fromText)\\nСтало: \\(toText)" : "Before: \\(fromText)\\nAfter: \\(toText)"
            } else {
                content.body = original.isEmpty ? (ru ? "Медиа" : "Media") : String(original.prefix(300))
            }
        } else {
            content.body = label
        }""",
        "history_notification_diff_text",
    )

    # 2. Add "История изменений" in message context menu on long press
    cm_path = src / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"
    _replace_once(
        cm_path,
        """            // Plugins belong to exteraGram: this opens the enabled plugins' actions for this chat.""",
        """            // Nowzen: quick "Edit & Delete History" on long press
            if !AyuDecoyMode.isActive, message.id.peerId.namespace != Namespaces.Peer.SecretChat {
                ayuActions.append(.action(ContextMenuActionItem(text: ru ? "История изменений" : "Edit history", icon: { theme in
                    return UIImage(systemName: "clock.arrow.circlepath")?.withTintColor(theme.contextMenu.primaryColor, renderingMode: .alwaysOriginal)
                }, action: { controller, _ in
                    controller?.dismiss(completion: {
                        let _ = (context.engine.messages.ayuMessageHistory() |> take(1) |> deliverOnMainQueue).startStandalone(next: { state in
                            let records = state.records.filter { $0.peerId == message.id.peerId.toInt64() && $0.messageId == message.id.id }
                            let title = ru ? "История изменений" : "Edit history"
                            let body: String
                            if records.isEmpty {
                                body = ru ? "Изменений или удалений для этого сообщения не зафиксировано." : "No edits or deletions recorded for this message."
                            } else {
                                let formatter = DateFormatter()
                                formatter.dateStyle = .short
                                formatter.timeStyle = .medium
                                body = records.map { rec in
                                    let dateStr = formatter.string(from: Date(timeIntervalSince1970: TimeInterval(rec.recordedAt)))
                                    let kindStr = rec.kind == .deleted ? (ru ? "Удалено" : "Deleted") : (ru ? "Изменено" : "Edited")
                                    let txt = rec.text.isEmpty ? (ru ? "[Медиа]" : "[Media]") : rec.text
                                    return "[\\(dateStr)] \\(kindStr):\\n\\(txt)"
                                }.joined(separator: "\\n\\n")
                            }
                            let alert = UIAlertController(title: title, message: body, preferredStyle: .alert)
                            alert.addAction(UIAlertAction(title: "OK", style: .default))
                            context.sharedContext.applicationBindings.presentNativeController(alert)
                        })
                    })
                })))
            }
            // Plugins belong to exteraGram: this opens the enabled plugins' actions for this chat.""",
        "context_menu_edit_history",
    )


def _enhance_message_shot_native_look(src: Path) -> None:
    canvas_path = src / "submodules/TelegramUI/Sources/Chat/AyuMessageShotCanvas.swift"
    _replace_once(
        canvas_path,
        """func ayuRenderMessageShot(cards: [AyuMessageShotCard], dark: Bool, width: CGFloat, maximumHeight: CGFloat, showBackground: Bool = true, showAuthors: Bool = true, showDate: Bool = true, showHeader: Bool = true) -> UIImage? {
    guard !cards.isEmpty, width.isFinite, maximumHeight.isFinite, width > 152.0, maximumHeight >= 200.0 else { return nil }
    let cardWidth = width - 112.0
    let innerWidth = cardWidth - 40.0
    var layouts: [(CGRect, CGRect, CGRect?)] = []
    var y: CGFloat = showHeader ? 90.0 : 24.0
    for card in cards {
        let measured = card.text.boundingRect(with: CGSize(width: innerWidth, height: maximumHeight), options: [.usesLineFragmentOrigin, .usesFontLeading], context: nil)
        guard measured.height.isFinite else { return nil }
        let textHeight = max(ceil(measured.height), 32.0)
        let x: CGFloat = card.outgoing ? 88.0 : 24.0
        let textFrame = CGRect(x: x + 20.0, y: y + (showAuthors ? 62.0 : 20.0), width: innerWidth, height: textHeight)
        var photoFrame: CGRect?
        var bottom = textFrame.maxY
        if let photo = card.photo, photo.size.width > 0.0, photo.size.height > 0.0 {
            let scale = min(innerWidth / photo.size.width, 360.0 / photo.size.height)
            let frame = CGRect(x: x + 20.0, y: bottom + 14.0, width: photo.size.width * scale, height: photo.size.height * scale)
            photoFrame = frame
            bottom = frame.maxY
        }
        let frame = CGRect(x: x, y: y, width: cardWidth, height: bottom - y + (showDate ? 54.0 : 20.0))
        layouts.append((frame, textFrame, photoFrame))
        y = frame.maxY + 20.0
        if y + 44.0 > maximumHeight { return nil }
    }
    let format = UIGraphicsImageRendererFormat()
    format.scale = 1.0
    format.opaque = showBackground
    let background = dark ? UIColor(red: 0.09, green: 0.08, blue: 0.13, alpha: 1.0) : UIColor(red: 0.94, green: 0.93, blue: 0.98, alpha: 1.0)
    let secondary = dark ? UIColor(white: 0.70, alpha: 1.0) : UIColor(white: 0.40, alpha: 1.0)
    return UIGraphicsImageRenderer(size: CGSize(width: width, height: ceil(y + 44.0)), format: format).image { rendererContext in
        if showBackground {
            background.setFill()
            UIBezierPath(rect: CGRect(x: 0.0, y: 0.0, width: width, height: ceil(y + 44.0))).fill()
        } else {
            rendererContext.cgContext.clear(CGRect(x: 0.0, y: 0.0, width: width, height: ceil(y + 44.0)))
        }
        if showHeader {
            ("AyuGram · MessageShot" as NSString).draw(at: CGPoint(x: 28.0, y: 28.0), withAttributes: [.font: UIFont.systemFont(ofSize: 30.0, weight: .semibold), .foregroundColor: secondary])
        }
        for (index, card) in cards.enumerated() {
            let (frame, textFrame, photoFrame) = layouts[index]
            let fill = dark ? UIColor(white: card.outgoing ? 0.23 : 0.16, alpha: 1.0) : (card.outgoing ? UIColor(red: 0.88, green: 0.84, blue: 0.98, alpha: 1.0) : .white)
            fill.setFill()
            UIBezierPath(roundedRect: frame, cornerRadius: 24.0).fill()
            if showAuthors {
                (card.author as NSString).draw(in: CGRect(x: frame.minX + 20.0, y: frame.minY + 16.0, width: innerWidth, height: 36.0), withAttributes: [.font: UIFont.systemFont(ofSize: 27.0, weight: .semibold), .foregroundColor: dark ? UIColor(red: 0.78, green: 0.69, blue: 1.0, alpha: 1.0) : UIColor(red: 0.36, green: 0.22, blue: 0.63, alpha: 1.0)])
            }
            card.text.draw(with: textFrame, options: [.usesLineFragmentOrigin, .usesFontLeading], context: nil)
            if let photoFrame, let photo = card.photo { photo.draw(in: photoFrame) }
            if showDate {
                (card.date as NSString).draw(in: CGRect(x: frame.minX + 20.0, y: frame.maxY - 36.0, width: innerWidth, height: 30.0), withAttributes: [.font: UIFont.systemFont(ofSize: 21.0), .foregroundColor: secondary])
            }
        }
    }
}""",
        """func ayuRenderMessageShot(cards: [AyuMessageShotCard], dark: Bool, width: CGFloat, maximumHeight: CGFloat, showBackground: Bool = true, showAuthors: Bool = true, showDate: Bool = true, showHeader: Bool = true) -> UIImage? {
    guard !cards.isEmpty, width.isFinite, maximumHeight.isFinite, width > 152.0, maximumHeight >= 200.0 else { return nil }
    let maxBubbleWidth = width * 0.78
    let horizontalPad: CGFloat = 18.0
    var layouts: [(CGRect, CGRect, CGRect?)] = []
    var y: CGFloat = 20.0
    for card in cards {
        let contentMaxW = maxBubbleWidth - horizontalPad * 2.0
        let measured = card.text.boundingRect(with: CGSize(width: contentMaxW, height: maximumHeight), options: [.usesLineFragmentOrigin, .usesFontLeading], context: nil)
        guard measured.height.isFinite else { return nil }
        let authorSize = showAuthors ? (card.author as NSString).boundingRect(with: CGSize(width: contentMaxW, height: 34.0), options: [.usesLineFragmentOrigin], attributes: [.font: UIFont.systemFont(ofSize: 22.0, weight: .semibold)], context: nil).size : .zero
        let dateWidth: CGFloat = showDate ? 110.0 : 0.0
        let textW = ceil(max(measured.width, authorSize.width))
        var bubbleW = min(maxBubbleWidth, max(textW + horizontalPad * 2.0 + (card.photo == nil ? 36.0 : 0.0), dateWidth + horizontalPad * 2.0))
        if card.photo != nil {
            bubbleW = max(bubbleW, min(maxBubbleWidth, 340.0))
        }
        let innerW = bubbleW - horizontalPad * 2.0
        let textH = max(ceil(measured.height), 26.0)
        let x: CGFloat = card.outgoing ? (width - bubbleW - 16.0) : 16.0
        let topPad: CGFloat = showAuthors ? 46.0 : 14.0
        let textFrame = CGRect(x: x + horizontalPad, y: y + topPad, width: innerW, height: textH)
        var photoFrame: CGRect?
        var bottom = textFrame.maxY
        if let photo = card.photo, photo.size.width > 0.0, photo.size.height > 0.0 {
            let scale = min(innerW / photo.size.width, 360.0 / photo.size.height)
            let frame = CGRect(x: x + horizontalPad, y: bottom + 10.0, width: photo.size.width * scale, height: photo.size.height * scale)
            photoFrame = frame
            bottom = frame.maxY
        }
        let frame = CGRect(x: x, y: y, width: bubbleW, height: bottom - y + (showDate ? 34.0 : 14.0))
        layouts.append((frame, textFrame, photoFrame))
        y = frame.maxY + 10.0
        if y + 24.0 > maximumHeight { return nil }
    }
    let totalHeight = ceil(y + 12.0)
    let format = UIGraphicsImageRendererFormat()
    format.scale = 1.0
    format.opaque = showBackground
    let background = dark ? UIColor(red: 0.06, green: 0.09, blue: 0.13, alpha: 1.0) : UIColor(red: 0.85, green: 0.91, blue: 0.84, alpha: 1.0)
    let secondary = dark ? UIColor(white: 0.70, alpha: 0.85) : UIColor(red: 0.35, green: 0.45, blue: 0.38, alpha: 0.9)
    return UIGraphicsImageRenderer(size: CGSize(width: width, height: totalHeight), format: format).image { rendererContext in
        if showBackground {
            background.setFill()
            UIBezierPath(rect: CGRect(x: 0.0, y: 0.0, width: width, height: totalHeight)).fill()
        } else {
            rendererContext.cgContext.clear(CGRect(x: 0.0, y: 0.0, width: width, height: totalHeight))
        }
        for (index, card) in cards.enumerated() {
            let (frame, textFrame, photoFrame) = layouts[index]
            let fill = dark
                ? (card.outgoing ? UIColor(red: 0.17, green: 0.32, blue: 0.47, alpha: 1.0) : UIColor(red: 0.10, green: 0.14, blue: 0.20, alpha: 1.0))
                : (card.outgoing ? UIColor(red: 0.93, green: 0.99, blue: 0.87, alpha: 1.0) : .white)
            fill.setFill()
            UIBezierPath(roundedRect: frame, cornerRadius: 22.0).fill()
            if showAuthors {
                let authorColor = dark ? UIColor(red: 0.43, green: 0.72, blue: 0.98, alpha: 1.0) : UIColor(red: 0.09, green: 0.49, blue: 0.85, alpha: 1.0)
                (card.author as NSString).draw(in: CGRect(x: frame.minX + horizontalPad, y: frame.minY + 12.0, width: frame.width - horizontalPad * 2.0, height: 28.0), withAttributes: [.font: UIFont.systemFont(ofSize: 22.0, weight: .semibold), .foregroundColor: authorColor])
            }
            card.text.draw(with: textFrame, options: [.usesLineFragmentOrigin, .usesFontLeading], context: nil)
            if let photoFrame, let photo = card.photo {
                rendererContext.cgContext.saveGState()
                UIBezierPath(roundedRect: photoFrame, cornerRadius: 14.0).addClip()
                photo.draw(in: photoFrame)
                rendererContext.cgContext.restoreGState()
            }
            if showDate {
                let timeStr = card.outgoing ? "\\(card.date) ✓✓" : card.date
                let style = NSMutableParagraphStyle()
                style.alignment = .right
                (timeStr as NSString).draw(in: CGRect(x: frame.minX + horizontalPad, y: frame.maxY - 28.0, width: frame.width - horizontalPad * 2.0, height: 22.0), withAttributes: [.font: UIFont.systemFont(ofSize: 17.0), .foregroundColor: secondary, .paragraphStyle: style])
            }
        }
    }
}""",
        "native_iphone_messageshot_render",
    )


def _enhance_settings_stability_and_grouping(src: Path) -> None:
    # Fix duplicate stableId == 35 in AyuExtrasController that caused ItemListNode crash/freeze
    extras_path = src / "submodules/SettingsUI/Sources/AyuExtrasController.swift"
    _replace_once(
        extras_path,
        """        let undoSeconds = UserDefaults.standard.integer(forKey: "ayu.extra.undoSendSeconds")
        entries.append(.link(4, 35, AyuSettingsIcons.symbol("arrow.uturn.backward.circle.fill", color: UIColor(rgb: 0x34C759)), ru ? "Отмена отправки" : "Undo send", undoSeconds == 0 ? (ru ? "выкл." : "off") : (ru ? "\\(undoSeconds) с" : "\\(undoSeconds) s")))""",
        """        let undoSeconds = UserDefaults.standard.integer(forKey: "ayu.extra.undoSendSeconds")
        entries.append(.link(4, 40, AyuSettingsIcons.symbol("arrow.uturn.backward.circle.fill", color: UIColor(rgb: 0x34C759)), ru ? "Отмена отправки" : "Undo send", undoSeconds == 0 ? (ru ? "выкл." : "off") : (ru ? "\\(undoSeconds) с" : "\\(undoSeconds) s")))""",
        "fix_extras_duplicate_id_35_entry",
    )
    _replace_once(
        extras_path,
        """        if id == 35 {""",
        """        if id == 40 {""",
        "fix_extras_duplicate_id_35_handler",
    )

    # Improve Russian labels and grouping in AyuCategoriesController
    cat_path = src / "submodules/SettingsUI/Sources/AyuCategoriesController.swift"
    _replace_once(
        cat_path,
        """    case .privacy:
        return [
            AyuCategoryItem(id: 1, symbol: "eye.slash.fill", color: 0x8E5CF7, titleRu: "Режим призрака", titleEn: "Ghost Mode", subtitleRu: "Прочтения, онлайн, набор, загрузка", subtitleEn: "Read receipts, online, typing, uploads", open: page { ayuGhostModeController(context: $0) }),
            AyuCategoryItem(id: 2, symbol: "eye.trianglebadge.exclamationmark.fill", color: 0x5856D6, titleRu: "Режим призрака+", titleEn: "Ghost Mode+", subtitleRu: "Тонкая настройка", subtitleEn: "Fine-tuning", open: page { ayuGhostModePlusController(context: $0) }),
            AyuCategoryItem(id: 3, symbol: "person.crop.circle.badge.checkmark", color: 0x8E5CF7, titleRu: "Призрак по чатам", titleEn: "Ghost Mode by chat", subtitleRu: "Включить или выключить в отдельных чатах", subtitleEn: "On or off in single chats", open: page { ayuGhostExceptionsController(context: $0) }),
            AyuCategoryItem(id: 4, symbol: "figure.walk.motion", color: 0x34C759, titleRu: "Активность и следы", titleEn: "Activity & traces", subtitleRu: "Статусы, всегда онлайн, прочитать локально, истории, номер", subtitleEn: "Statuses, always online, read locally, stories, number", open: page { ayuPrivacyPlusController(context: $0) }),
            AyuCategoryItem(id: 5, symbol: "hand.raised.fill", color: 0x34C759, titleRu: "Приватность и мелочи", titleEn: "Privacy & extras", subtitleRu: "Метаданные фото, чистые ссылки, анти-скам, звонки", subtitleEn: "Photo metadata, clean links, anti-scam, calls", open: page { ayuExtrasController(context: $0) })
        ]""",
        """    case .privacy:
        return [
            AyuCategoryItem(id: 1, symbol: "eye.slash.fill", color: 0x8E5CF7, titleRu: "Режим призрака", titleEn: "Ghost Mode", subtitleRu: "Общий тумблер, чтение, онлайн, истории", subtitleEn: "Global switch, read receipts, online, stories", open: page { ayuGhostModeController(context: $0) }),
            AyuCategoryItem(id: 2, symbol: "eye.trianglebadge.exclamationmark.fill", color: 0x5856D6, titleRu: "Тонкая настройка призрака", titleEn: "Ghost Mode+", subtitleRu: "Исключения и призрак по чатам", subtitleEn: "Fine-tuning & per-chat rules", open: page { ayuGhostModePlusController(context: $0) }),
            AyuCategoryItem(id: 3, symbol: "person.crop.circle.badge.checkmark", color: 0x8E5CF7, titleRu: "Призрак по чатам", titleEn: "Ghost Mode by chat", subtitleRu: "Переопределить для отдельных чатов", subtitleEn: "On or off in single chats", open: page { ayuGhostExceptionsController(context: $0) }),
            AyuCategoryItem(id: 4, symbol: "figure.walk.motion", color: 0x34C759, titleRu: "Активность и анонимность", titleEn: "Activity & traces", subtitleRu: "Статусы, истории, локальное чтение, номер", subtitleEn: "Statuses, stories, read locally, number", open: page { ayuPrivacyPlusController(context: $0) }),
            AyuCategoryItem(id: 5, symbol: "lock.shield.fill", color: 0xFF9500, titleRu: "Защита чатов и Face ID", titleEn: "Chat protection", subtitleRu: "Face ID на чаты, скрытые чаты, скриншоты", subtitleEn: "Face ID chats, hidden chats, screenshots", open: page { ayuChatProtectionController(context: $0) }),
            AyuCategoryItem(id: 6, symbol: "theatermasks.fill", color: 0x5856D6, titleRu: "Чистый Telegram (приманка)", titleEn: "Clean Telegram (Decoy)", subtitleRu: "Скрыть все функции Nowzen и второй аккаунт", subtitleEn: "Hide Nowzen features or use decoy account", open: page { ayuDecoySettingsController(context: $0) }),
            AyuCategoryItem(id: 7, symbol: "hand.raised.fill", color: 0x34C759, titleRu: "Дополнительная приватность", titleEn: "Privacy & extras", subtitleRu: "Метаданные, чистые ссылки, уведомления об удалениях", subtitleEn: "Metadata, clean links, deletion alerts", open: page { ayuExtrasController(context: $0) })
        ]""",
        "reorganize_privacy_category_items",
    )


def apply_nowzen_enhancements(src: Path) -> None:
    _enhance_app_delegate(src)
    _enhance_app_extras_defaults(src)
    _enhance_chat_privacy_and_face_id(src)
    _enhance_ghost_mode_and_stories(src)
    _enhance_deleted_and_view_once_media(src)
    _enhance_history_notifications_and_context_menu(src)
    _enhance_message_shot_native_look(src)
    _enhance_settings_stability_and_grouping(src)
