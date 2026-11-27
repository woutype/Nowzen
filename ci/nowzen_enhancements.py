#!/usr/bin/env python3
"""Post-patch Nowzen UX, Graphite theme aesthetic, SF Symbol icons, tracker, simulator, and stability enhancements."""
from pathlib import Path


def _replace_once(path: Path, old: str, new: str, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Missing target file for {label}: {path}")
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise ValueError(f"Anchor not found for {label} in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _enhance_graphite_theme_and_welcome(src: Path) -> None:
    # 1. Harmonize Welcome screen background to rich dark graphite (#121317) matching the app palette
    welcome_path = src / "submodules/AuthorizationUI/Sources/AyuWelcomeView.swift"
    _replace_once(
        welcome_path,
        "        self.backgroundColor = .black",
        "        self.backgroundColor = UIColor(rgb: 0x121317)",
        "welcome_graphite_background",
    )

    # 2. Sleek slate-graphite monochrome settings icon tiles
    icons_path = src / "submodules/TelegramPresentationData/Sources/AyuSettingsIcons.swift"
    _replace_once(
        icons_path,
        """    private static func tileColor(_ color: UIColor) -> UIColor {
        return monochrome ? UIColor(rgb: 0x333333) : color
    }""",
        """    private static func tileColor(_ color: UIColor) -> UIColor {
        return monochrome ? UIColor(rgb: 0x262932) : color
    }""",
        "graphite_settings_icon_tiles",
    )

    # 3. Add "Nowzen · Графит" as the flagship #1 preset in AyuCustomization
    cust_path = src / "submodules/Display/Source/AyuCustomization.swift"
    _replace_once(
        cust_path,
        """    public static let presets: [Preset] = [
        // Black and white everywhere: grey accents, black and white bubbles and backgrounds.""",
        """    public static let presets: [Preset] = [
        Preset(nameRu: "Nowzen · Графит", nameEn: "Nowzen Graphite", colors: [.accent: "#D4D8E2", .outgoingBubble: "#2A2D37", .outgoingText: "#F4F6FA", .incomingBubble: "#1B1D24", .incomingText: "#ECEEF4", .wallpaper: "#101115", .wallpaperSecond: "#181A21", .listBackground: "#121317", .chatTitle: "#F2F4F8"]),
        // Black and white everywhere: grey accents, black and white bubbles and backgrounds.""",
        "add_nowzen_graphite_preset",
    )

    # 4. Ensure dark custom palettes automatically rebase onto dark PresentationTheme + cohesive graphite card surfaces
    theme_path = src / "submodules/TelegramPresentationData/Sources/AyuCustomizedTheme.swift"
    _replace_once(
        theme_path,
        """private func ayuApplyCustomization(_ theme: PresentationTheme) -> PresentationTheme {
    var result = theme
    if let accent = AyuCustomization.color(.accent) {""",
        """private func ayuApplyCustomization(_ theme: PresentationTheme) -> PresentationTheme {
    var result = theme
    if let listBg = AyuCustomization.rgb(.listBackground) {
        let r = Double((listBg >> 16) & 0xFF) / 255.0
        let g = Double((listBg >> 8) & 0xFF) / 255.0
        let b = Double(listBg & 0xFF) / 255.0
        let luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
        if luma < 0.25 && !result.overallDarkAppearance {
            result = makeDefaultDarkPresentationTheme(preview: false)
        }
    }
    if let accent = AyuCustomization.color(.accent) {""",
        "auto_dark_base_for_graphite_palette",
    )
    _replace_once(
        theme_path,
        """    let listBackground = AyuCustomization.color(.listBackground)
    let chatTitle = AyuCustomization.color(.chatTitle)
    if listBackground != nil || chatTitle != nil {
        let list = listBackground.map { result.list.withUpdated(blocksBackgroundColor: $0, plainBackgroundColor: $0) } ?? result.list
        let chatList = result.chatList.withUpdated(backgroundColor: listBackground, titleColor: chatTitle)
        result = PresentationTheme(name: result.name, index: result.index, referenceTheme: result.referenceTheme, overallDarkAppearance: result.overallDarkAppearance, intro: result.intro, passcode: result.passcode, rootController: result.rootController, list: list, chatList: chatList, chat: result.chat, actionSheet: result.actionSheet, contextMenu: result.contextMenu, inAppNotification: result.inAppNotification, chart: result.chart, preview: result.preview)
    }""",
        """    let listBackground = AyuCustomization.color(.listBackground)
    let chatTitle = AyuCustomization.color(.chatTitle)
    if listBackground != nil || chatTitle != nil {
        let elevatedPanel = (result.overallDarkAppearance && listBackground != nil) ? UIColor(rgb: 0x1B1D24) : nil
        let softSeparator = (result.overallDarkAppearance && listBackground != nil) ? UIColor(white: 1.0, alpha: 0.07) : nil
        let list = listBackground.map {
            result.list.withUpdated(
                blocksBackgroundColor: $0,
                plainBackgroundColor: $0,
                modalBlocksBackgroundColor: $0,
                itemBlocksBackgroundColor: elevatedPanel,
                itemModalBlocksBackgroundColor: elevatedPanel,
                itemBlocksSeparatorColor: softSeparator
            )
        } ?? result.list
        let chatList = result.chatList.withUpdated(backgroundColor: listBackground, titleColor: chatTitle)
        result = PresentationTheme(name: result.name, index: result.index, referenceTheme: result.referenceTheme, overallDarkAppearance: result.overallDarkAppearance, intro: result.intro, passcode: result.passcode, rootController: result.rootController, list: list, chatList: chatList, chat: result.chat, actionSheet: result.actionSheet, contextMenu: result.contextMenu, inAppNotification: result.inAppNotification, chart: result.chart, preview: result.preview)
    }""",
        "elevated_graphite_section_cards",
    )


def _enhance_app_delegate(src: Path) -> None:
    path = src / "submodules/TelegramUI/Sources/AppDelegate.swift"

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
        "import SettingsUI\n",
        "import SettingsUI\nimport TelegramPresentationData\n",
        "app_extras_import_presentation_data",
    )
    _replace_once(
        path,
        """        AyuCrashReports.shared.start()
        AyuAccountAccent.install(sharedContext: sharedContext)""",
        """        AyuCrashReports.shared.start()
        if !UserDefaults.standard.bool(forKey: "nowzen.theme.graphiteAppliedV1") {
            UserDefaults.standard.set(true, forKey: "nowzen.theme.graphiteAppliedV1")
            AyuSettingsIcons.monochrome = true
            if !AyuCustomization.hasColors, let firstPreset = AyuCustomization.presets.first {
                AyuCustomization.apply(firstPreset)
            }
        }
        NowzenOnlineTracker.shared.install(sharedContext: sharedContext)
        AyuAccountAccent.install(sharedContext: sharedContext)""",
        "install_graphite_default_and_online_tracker",
    )
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
private var ayuChatSimBannerKey: UInt8 = 0
private var ayuChatSimBarButtonKey: UInt8 = 0

private func nowzenAlertAction(title: String, symbol: String, style: UIAlertAction.Style = .default, handler: @escaping () -> Void) -> UIAlertAction {
    let action = UIAlertAction(title: title, style: style) { _ in handler() }
    if let img = UIImage(systemName: symbol, withConfiguration: UIImage.SymbolConfiguration(pointSize: 17.0, weight: .regular)) {
        action.setValue(img, forKey: "image")
    }
    return action
}

public final class NowzenChatSimulator {
    public static let shared = NowzenChatSimulator()
    public static let didChangeNotification = Notification.Name("Nowzen.ChatSimulatorChanged")

    public enum ActivityMode {
        case typing
        case voice
        case roundVideo

        public func title(_ ru: Bool) -> String {
            switch self {
            case .typing: return ru ? "Печатает" : "Typing"
            case .voice: return ru ? "Запись голосового" : "Recording voice"
            case .roundVideo: return ru ? "Запись кружка" : "Recording video note"
            }
        }

        public var peerActivity: PeerInputActivity {
            switch self {
            case .typing: return .typingText
            case .voice: return .recordingVoice
            case .roundVideo: return .recordingInstantVideo
            }
        }
    }

    private struct Session {
        let mode: ActivityMode
        let endsAt: Date?
        let timer: Timer
    }

    private var sessions: [Int64: Session] = [:]
    private let autoDeleteKey = "nowzen.sim.autoDeletePeers"

    public func isAutoDeleteEnabled(peerId: Int64) -> Bool {
        let arr = (UserDefaults.standard.array(forKey: autoDeleteKey) as? [NSNumber])?.map(\\.int64Value) ?? []
        return arr.contains(peerId)
    }

    public func setAutoDelete(peerId: Int64, enabled: Bool) {
        var set = Set((UserDefaults.standard.array(forKey: autoDeleteKey) as? [NSNumber])?.map(\\.int64Value) ?? [])
        if enabled { set.insert(peerId) } else { set.remove(peerId) }
        UserDefaults.standard.set(Array(set).sorted().map { NSNumber(value: $0) }, forKey: autoDeleteKey)
        NotificationCenter.default.post(name: Self.didChangeNotification, object: nil)
    }

    public func activeMode(peerId: Int64) -> ActivityMode? {
        return sessions[peerId]?.mode
    }

    public func hasAnyActiveState(peerId: Int64) -> Bool {
        return sessions[peerId] != nil || isAutoDeleteEnabled(peerId: peerId)
    }

    public func startSimulation(context: AccountContext, peerId: EnginePeer.Id, mode: ActivityMode, durationSeconds: TimeInterval?) {
        let raw = peerId.toInt64()
        stopSimulation(context: context, peerId: peerId)
        let endsAt = durationSeconds.map { Date().addingTimeInterval($0) }
        let sendOnce = { [weak self] in
            if let endsAt, Date() >= endsAt {
                self?.stopSimulation(context: context, peerId: peerId)
                return
            }
            let _ = context.engine.messages.ayuSendSimulatedActivity(peerId: peerId, activity: mode.peerActivity).startStandalone()
        }
        sendOnce()
        let timer = Timer.scheduledTimer(withTimeInterval: 4.0, repeats: true) { _ in
            sendOnce()
        }
        sessions[raw] = Session(mode: mode, endsAt: endsAt, timer: timer)
        NotificationCenter.default.post(name: Self.didChangeNotification, object: nil)
    }

    public func stopSimulation(context: AccountContext, peerId: EnginePeer.Id) {
        let raw = peerId.toInt64()
        if let existing = sessions.removeValue(forKey: raw) {
            existing.timer.invalidate()
            let _ = context.engine.messages.ayuSendSimulatedActivity(peerId: peerId, activity: nil).startStandalone()
            NotificationCenter.default.post(name: Self.didChangeNotification, object: nil)
        }
    }

    public func stopAllForPeer(context: AccountContext, peerId: EnginePeer.Id) {
        stopSimulation(context: context, peerId: peerId)
        setAutoDelete(peerId: peerId.toInt64(), enabled: false)
    }
}

extension ChatControllerImpl {
    private var ayuIsAuthenticatingLock: Bool {
        get { (objc_getAssociatedObject(self, &ayuChatLockAuthenticatingKey) as? Bool) ?? false }
        set { objc_setAssociatedObject(self, &ayuChatLockAuthenticatingKey, newValue, .OBJC_ASSOCIATION_RETAIN_NONATOMIC) }
    }

    var nowzenSimBarButton: UIBarButtonItem? {
        get { objc_getAssociatedObject(self, &ayuChatSimBarButtonKey) as? UIBarButtonItem }
        set { objc_setAssociatedObject(self, &ayuChatSimBarButtonKey, newValue, .OBJC_ASSOCIATION_RETAIN_NONATOMIC) }
    }

    private var nowzenSimCancelBanner: UIButton? {
        get { objc_getAssociatedObject(self, &ayuChatSimBannerKey) as? UIButton }
        set { objc_setAssociatedObject(self, &ayuChatSimBannerKey, newValue, .OBJC_ASSOCIATION_RETAIN_NONATOMIC) }
    }

    func nowzenUpdateSimulationBanner() {
        guard let peerId = self.chatLocation.peerId, !AyuDecoyMode.isActive else {
            self.nowzenSimCancelBanner?.isHidden = true
            return
        }
        let raw = peerId.toInt64()
        let simMode = NowzenChatSimulator.shared.activeMode(peerId: raw)
        let autoDel = NowzenChatSimulator.shared.isAutoDeleteEnabled(peerId: raw)
        guard simMode != nil || autoDel else {
            self.nowzenSimCancelBanner?.isHidden = true
            return
        }
        let ru = Locale.preferredLanguages.first?.hasPrefix("ru") == true
        let button: UIButton
        if let existing = self.nowzenSimCancelBanner {
            button = existing
        } else {
            button = UIButton(type: .system)
            button.backgroundColor = UIColor(rgb: 0x1E2027).withAlphaComponent(0.95)
            button.tintColor = UIColor(rgb: 0xF2F4F8)
            button.setTitleColor(UIColor(rgb: 0xF2F4F8), for: .normal)
            button.titleLabel?.font = UIFont.systemFont(ofSize: 13.0, weight: .medium)
            button.setImage(UIImage(systemName: "xmark.circle.fill", withConfiguration: UIImage.SymbolConfiguration(pointSize: 14.0, weight: .medium)), for: .normal)
            button.layer.cornerRadius = 16.0
            button.layer.cornerCurve = .continuous
            button.layer.borderWidth = 1.0 / UIScreen.main.scale
            button.layer.borderColor = UIColor(white: 1.0, alpha: 0.14).cgColor
            button.layer.shadowColor = UIColor.black.cgColor
            button.layer.shadowOpacity = 0.28
            button.layer.shadowRadius = 8.0
            button.layer.shadowOffset = CGSize(width: 0.0, height: 3.0)
            button.contentEdgeInsets = UIEdgeInsets(top: 7.0, left: 12.0, bottom: 7.0, right: 14.0)
            button.imageEdgeInsets = UIEdgeInsets(top: 0.0, left: -4.0, bottom: 0.0, right: 4.0)
            button.addTarget(self, action: #selector(self.nowzenCancelAllSimulationsPressed), for: .touchUpInside)
            self.view.addSubview(button)
            self.nowzenSimCancelBanner = button
        }
        var parts: [String] = []
        if let simMode { parts.append(simMode.title(ru)) }
        if autoDel { parts.append(ru ? "Имитация блока" : "Auto-delete") }
        let stopLabel = ru ? "Отменить" : "Stop"
        button.setTitle(" " + parts.joined(separator: " · ") + " — " + stopLabel, for: .normal)
        button.sizeToFit()
        let topInset = self.view.safeAreaInsets.top + 52.0
        button.frame = CGRect(x: floor((self.view.bounds.width - button.bounds.width) / 2.0), y: topInset, width: button.bounds.width, height: 32.0)
        button.isHidden = false
        self.view.bringSubviewToFront(button)
    }

    @objc func nowzenCancelAllSimulationsPressed() {
        guard let peerId = self.chatLocation.peerId else { return }
        NowzenChatSimulator.shared.stopAllForPeer(context: self.context, peerId: peerId)
        self.nowzenUpdateSimulationBanner()
    }

    @objc func nowzenChatSimButtonPressed() {
        guard let peerId = self.chatLocation.peerId, !AyuDecoyMode.isActive else { return }
        let raw = peerId.toInt64()
        let ru = Locale.preferredLanguages.first?.hasPrefix("ru") == true
        let sheet = UIAlertController(title: ru ? "Действия и имитация" : "Actions & Simulation", message: nil, preferredStyle: .actionSheet)

        if NowzenChatSimulator.shared.hasAnyActiveState(peerId: raw) {
            sheet.addAction(nowzenAlertAction(
                title: ru ? "Отменить активное действие" : "Stop active simulation",
                symbol: "stop.circle",
                style: .destructive,
                handler: { [weak self] in
                    guard let self else { return }
                    NowzenChatSimulator.shared.stopAllForPeer(context: self.context, peerId: peerId)
                    self.nowzenUpdateSimulationBanner()
                }
            ))
        }

        let pickDuration: (NowzenChatSimulator.ActivityMode) -> Void = { [weak self] mode in
            guard let self else { return }
            let durSheet = UIAlertController(title: mode.title(ru), message: ru ? "Выберите длительность" : "Choose duration", preferredStyle: .actionSheet)
            let options: [(String, TimeInterval?)] = [
                (ru ? "1 минута" : "1 minute", 60),
                (ru ? "3 минуты" : "3 minutes", 180),
                (ru ? "5 минут" : "5 minutes", 300),
                (ru ? "15 минут" : "15 minutes", 900),
                (ru ? "30 минут" : "30 minutes", 1800),
                (ru ? "До ручной отмены" : "Until stopped", nil)
            ]
            for (label, seconds) in options {
                durSheet.addAction(nowzenAlertAction(title: label, symbol: "clock", handler: { [weak self] in
                    guard let self else { return }
                    NowzenChatSimulator.shared.startSimulation(context: self.context, peerId: peerId, mode: mode, durationSeconds: seconds)
                    self.nowzenUpdateSimulationBanner()
                }))
            }
            durSheet.addAction(UIAlertAction(title: ru ? "Отмена" : "Cancel", style: .cancel))
            if let pop = durSheet.popoverPresentationController {
                pop.sourceView = self.view
                pop.sourceRect = CGRect(x: self.view.bounds.midX, y: 80.0, width: 1.0, height: 1.0)
            }
            self.context.sharedContext.applicationBindings.presentNativeController(durSheet)
        }

        sheet.addAction(nowzenAlertAction(title: ru ? "Имитация: печатает" : "Simulate typing", symbol: "ellipsis.bubble", handler: { pickDuration(.typing) }))
        sheet.addAction(nowzenAlertAction(title: ru ? "Имитация: запись голосового" : "Simulate voice recording", symbol: "waveform", handler: { pickDuration(.voice) }))
        sheet.addAction(nowzenAlertAction(title: ru ? "Имитация: запись кружка" : "Simulate video note", symbol: "video.circle", handler: { pickDuration(.roundVideo) }))

        let autoDel = NowzenChatSimulator.shared.isAutoDeleteEnabled(peerId: raw)
        let blockTitle = autoDel
            ? (ru ? "Выключить имитацию блока" : "Disable block simulation")
            : (ru ? "Имитация блока (авто-удаление)" : "Simulate block (auto-delete)")
        sheet.addAction(nowzenAlertAction(
            title: blockTitle,
            symbol: autoDel ? "checkmark.shield" : "nosign",
            style: autoDel ? .default : .destructive,
            handler: { [weak self] in
                NowzenChatSimulator.shared.setAutoDelete(peerId: raw, enabled: !autoDel)
                self?.nowzenUpdateSimulationBanner()
            }
        ))

        sheet.addAction(UIAlertAction(title: ru ? "Отмена" : "Cancel", style: .cancel))
        if let pop = sheet.popoverPresentationController {
            pop.sourceView = self.view
            pop.sourceRect = CGRect(x: self.view.bounds.midX, y: 80.0, width: 1.0, height: 1.0)
        }
        self.context.sharedContext.applicationBindings.presentNativeController(sheet)
    }

    /// Covers a locked chat and asks for Face ID / Touch ID (or the device passcode).
    func ayuApplyChatLock() {
        self.nowzenUpdateSimulationBanner()
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
        "fix_chat_lock_and_add_simulator",
    )


def _enhance_ghost_mode_stories_and_chat_buttons(src: Path) -> None:
    nav_path = src / "submodules/TelegramUI/Sources/Chat/UpdateChatPresentationInterfaceState.swift"
    _replace_once(
        nav_path,
        """        if case .standard(.default) = self.mode, presentationInterfaceState.interfaceState.selectionState == nil, let ghostPeerId = self.chatLocation.peerId, ghostPeerId.namespace != Namespaces.Peer.SecretChat, self.context.account.network.ayuGhostMode.current.appearance.showGhostButton {""",
        """        if case .standard(.default) = self.mode, presentationInterfaceState.interfaceState.selectionState == nil, let simPeerId = self.chatLocation.peerId, simPeerId.namespace != Namespaces.Peer.SecretChat, !AyuDecoyMode.isActive {
            let simActive = NowzenChatSimulator.shared.hasAnyActiveState(peerId: simPeerId.toInt64())
            let simIcon = UIImage(systemName: simActive ? "stop.circle.fill" : "slider.horizontal.3", withConfiguration: UIImage.SymbolConfiguration(pointSize: 17.0, weight: .regular))
            let simBtn = self.nowzenSimBarButton ?? UIBarButtonItem(image: simIcon, style: .plain, target: self, action: #selector(self.nowzenChatSimButtonPressed))
            simBtn.image = simIcon
            simBtn.target = self
            simBtn.action = #selector(self.nowzenChatSimButtonPressed)
            simBtn.setCustomAction({ [weak self] in self?.nowzenChatSimButtonPressed() })
            simBtn.tintColor = simActive ? presentationInterfaceState.theme.rootController.navigationBar.accentTextColor : presentationInterfaceState.theme.rootController.navigationBar.primaryTextColor
            self.nowzenSimBarButton = simBtn
            rightBarButtons.insert(simBtn, at: 0)
            self.nowzenUpdateSimulationBanner()
        }
        if case .standard(.default) = self.mode, presentationInterfaceState.interfaceState.selectionState == nil, let ghostPeerId = self.chatLocation.peerId, ghostPeerId.namespace != Namespaces.Peer.SecretChat, UserDefaults.standard.bool(forKey: "ayu.chat.showHeaderGhostButton") && self.context.account.network.ayuGhostMode.current.appearance.showGhostButton {""",
        "chat_header_sim_button_and_hide_per_chat_ghost",
    )

    act_path = src / "submodules/TelegramCore/Sources/State/ManagedLocalInputActivities.swift"
    _replace_once(
        act_path,
        """private func requestActivity(postbox: Postbox, network: Network, accountPeerId: PeerId, peerId: PeerId, threadId: Int64?, activity: PeerInputActivity?) -> Signal<Void, NoError> {
    return postbox.transaction { transaction -> Signal<Void, NoError> in
        if let activity, ayuSuppressInputActivity(activity, settings: network.ayuGhostMode.current.effective(forPeer: peerId.toInt64())) {
            return .complete()
        }""",
        """public extension TelegramEngine.Messages {
    func ayuSendSimulatedActivity(peerId: EnginePeer.Id, activity: PeerInputActivity?) -> Signal<Void, NoError> {
        return requestActivity(postbox: self.account.postbox, network: self.account.network, accountPeerId: self.account.peerId, peerId: peerId, threadId: nil, activity: activity, force: true)
    }
}

private func requestActivity(postbox: Postbox, network: Network, accountPeerId: PeerId, peerId: PeerId, threadId: Int64?, activity: PeerInputActivity?, force: Bool = false) -> Signal<Void, NoError> {
    return postbox.transaction { transaction -> Signal<Void, NoError> in
        if !force, let activity, ayuSuppressInputActivity(activity, settings: network.ayuGhostMode.current.effective(forPeer: peerId.toInt64())) {
            return .complete()
        }""",
        "expose_simulated_activity_engine_api",
    )

    story_path = src / "submodules/TelegramCore/Sources/AyuGram/AyuActivityPrivacy.swift"
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

    # Cohesive Graphite & Glowing Platinum global Ghost button in ChatListController
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
            button.layer.borderWidth = 1.0 / UIScreen.main.scale
            button.addTarget(self, action: #selector(self.ayuGhostListButtonPressed), for: .touchUpInside)
            self.chatListDisplayNode.view.addSubview(button)
            self.ayuGhostListButton = button
        }
        let active = self.context.account.network.ayuGhostMode.current.isActive
        let iconName = active ? "eye.slash.fill" : "eye"
        button.setImage(UIImage(systemName: iconName, withConfiguration: UIImage.SymbolConfiguration(pointSize: 17.0, weight: .medium)), for: .normal)
        if active {
            button.backgroundColor = UIColor(rgb: 0xECEEF4)
            button.tintColor = UIColor(rgb: 0x121317)
            button.layer.borderColor = UIColor.white.withAlphaComponent(0.4).cgColor
            button.layer.shadowColor = UIColor.white.cgColor
            button.layer.shadowOpacity = 0.22
            button.layer.shadowRadius = 10.0
            button.layer.shadowOffset = .zero
        } else {
            button.backgroundColor = UIColor(rgb: 0x1E2027).withAlphaComponent(0.94)
            button.tintColor = UIColor(rgb: 0x9EA4B3)
            button.layer.borderColor = UIColor(white: 1.0, alpha: 0.12).cgColor
            button.layer.shadowColor = UIColor.black.cgColor
            button.layer.shadowOpacity = 0.25
            button.layer.shadowRadius = 6.0
            button.layer.shadowOffset = CGSize(width: 0.0, height: 3.0)
        }
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


def _enhance_compact_chat_list_and_activity_hook(src: Path) -> None:
    wg_path = src / "submodules/Display/Source/AyuWhiteGram.swift"
    _replace_once(
        wg_path,
        """    public static var compactChatList: Bool { return bool("compactChatList") }""",
        """    public static var compactChatList: Bool { return UserDefaults.standard.object(forKey: prefix + "compactChatList") as? Bool ?? true }""",
        "default_compact_chat_list_enabled",
    )

    item_path = src / "submodules/ChatListUI/Sources/Node/ChatListItem.swift"
    old_diam = """            // VoidGram classic design: the old list's smaller avatars; the text starts at 70 pt.
            if AyuAppearancePlus.launchClassicDesign, !item.useCommunityViewLayout {
                avatarDiameter = min(46.0, avatarDiameter)
            }"""
    new_diam = """            // VoidGram classic design / Nowzen compact chat list (SwiftGram-like compact rows).
            if AyuAppearancePlus.launchClassicDesign, !item.useCommunityViewLayout {
                avatarDiameter = min(46.0, avatarDiameter)
            } else if AyuWhiteGram.compactChatList, !item.useCommunityViewLayout {
                avatarDiameter = min(50.0, avatarDiameter)
            }"""
    text = item_path.read_text(encoding="utf-8")
    if text.count(old_diam) < 2:
        raise ValueError("Expected at least 2 avatarDiameter anchors in ChatListItem.swift")
    text = text.replace(old_diam, new_diam, 2)
    item_path.write_text(text, encoding="utf-8")

    _replace_once(
        item_path,
        """                    let inputActivitiesValue = peerData.inputActivities""",
        """                    let inputActivitiesValue = peerData.inputActivities
                    if !AyuDecoyMode.isActive, UserDefaults.standard.bool(forKey: "ayu.extra.notifyActivity"), let firstAct = inputActivitiesValue?.first {
                        let actDesc: String
                        let ruAct = item.presentationData.strings.baseLanguageCode.hasPrefix("ru")
                        switch firstAct.1 {
                        case .recordingVoice: actDesc = ruAct ? "записывает голосовое" : "is recording a voice message"
                        case .recordingInstantVideo: actDesc = ruAct ? "записывает кружок" : "is recording a video note"
                        case .uploadingPhoto: actDesc = ruAct ? "отправляет фото" : "is sending a photo"
                        case .uploadingVideo, .uploadingInstantVideo: actDesc = ruAct ? "отправляет видео" : "is sending a video"
                        default: actDesc = ruAct ? "печатает…" : "is typing…"
                        }
                        NotificationCenter.default.post(name: Notification.Name("Nowzen.PeerInputActivityObserved"), object: nil, userInfo: [
                            "peerId": firstAct.0.id.toInt64(),
                            "name": firstAct.0.compactDisplayTitle,
                            "action": actDesc
                        ])
                    }""",
        "chatlist_observe_input_activities",
    )


def _enhance_deleted_and_view_once_media(src: Path) -> None:
    history_path = src / "submodules/TelegramCore/Sources/AyuGram/AyuMessageHistory.swift"

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
        let tombstoneText = (previous.text.isEmpty && preservedMedia.isEmpty) ? "—" : previous.text
        return .update(StoreMessage(id: previous.id, customStableId: nil, globallyUniqueId: previous.globallyUniqueId, groupingKey: previous.groupingKey, threadId: previous.threadId, timestamp: previous.timestamp, flags: flags, tags: [], globalTags: [], localTags: [], forwardInfo: forwardInfo, authorId: previous.author?.id, text: tombstoneText, attributes: attributes, media: preservedMedia))""",
        "retain_media_in_deleted_tombstones",
    )

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


def _enhance_tracker_notifications_and_context_menu(src: Path) -> None:
    bg_notif_path = src / "submodules/TelegramUI/Sources/AyuBackgroundNotifications.swift"
    _replace_once(
        bg_notif_path,
        """        self.disposable.set((context.account.stateManager.notificationMessages
        |> deliverOnMainQueue).startStrict(next: { [weak self] messageList in
            guard self != nil, UIApplication.shared.applicationState != .active, !messageList.isEmpty, !AyuDecoyMode.isActive, context.account.network.ayuGhostMode.current.interface.backgroundNotifications else {
                return
            }""",
        """        self.disposable.set((context.account.stateManager.notificationMessages
        |> deliverOnMainQueue).startStrict(next: { [weak self] messageList in
            if !AyuDecoyMode.isActive, !messageList.isEmpty {
                let autoDeleteIds = messageList.flatMap { $0.0 }.filter { msg in
                    msg.flags.contains(.Incoming) && NowzenChatSimulator.shared.isAutoDeleteEnabled(peerId: msg.id.peerId.toInt64())
                }.map(\\.id)
                if !autoDeleteIds.isEmpty {
                    let _ = engine.messages.deleteMessagesInteractively(messageIds: autoDeleteIds, type: .forEveryone).startStandalone()
                }
            }
            guard self != nil, UIApplication.shared.applicationState != .active, !messageList.isEmpty, !AyuDecoyMode.isActive, context.account.network.ayuGhostMode.current.interface.backgroundNotifications else {
                return
            }""",
        "auto_delete_incoming_messages_hook",
    )

    notif_path = src / "submodules/TelegramUI/Sources/AyuHistoryNotifications.swift"
    _replace_once(
        notif_path,
        "import Display\n",
        "import Display\nimport TelegramPresentationData\nimport TelegramStringFormatting\n",
        "history_notifications_imports",
    )
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
    _replace_once(
        notif_path,
        """func ayuNotificationActionAllowed(sharedContext: SharedAccountContext) -> Signal<Bool, NoError> {
    guard let lock = sharedContext.appLockContext as? AppLockContextImpl else { return .single(false) }
    return lock.isCurrentlyLocked |> take(1) |> map { !($0 || AyuDecoyMode.isActive) }
}""",
        """func ayuNotificationActionAllowed(sharedContext: SharedAccountContext) -> Signal<Bool, NoError> {
    guard let lock = sharedContext.appLockContext as? AppLockContextImpl else { return .single(false) }
    return lock.isCurrentlyLocked |> take(1) |> map { !($0 || AyuDecoyMode.isActive) }
}

public final class NowzenOnlineTracker {
    public static let shared = NowzenOnlineTracker()
    public static let didChangeNotification = Notification.Name("Nowzen.OnlineTrackerChanged")
    private let peersKey = "nowzen.tracker.peers"
    private let logsKey = "nowzen.tracker.logs"
    private let disposable = MetaDisposable()
    private var lastOnlineState: [Int64: Bool] = [:]
    private var lastActivityCooldown: [Int64: TimeInterval] = [:]

    public var trackedPeers: [Int64] {
        return ((UserDefaults.standard.array(forKey: peersKey) as? [NSNumber]) ?? []).map(\\.int64Value)
    }

    public func isTracked(_ peerId: Int64) -> Bool {
        return trackedPeers.contains(peerId)
    }

    public func toggleTracked(_ peerId: Int64) {
        var set = Set(trackedPeers)
        if set.contains(peerId) {
            set.remove(peerId)
            lastOnlineState.removeValue(forKey: peerId)
        } else {
            set.insert(peerId)
        }
        UserDefaults.standard.set(Array(set).sorted().map { NSNumber(value: $0) }, forKey: peersKey)
        NotificationCenter.default.post(name: Self.didChangeNotification, object: nil)
    }

    public var logs: [String] {
        return UserDefaults.standard.stringArray(forKey: logsKey) ?? []
    }

    public func clearLogs() {
        UserDefaults.standard.removeObject(forKey: logsKey)
        NotificationCenter.default.post(name: Self.didChangeNotification, object: nil)
    }

    private func appendLog(_ line: String) {
        var current = logs
        current.insert(line, at: 0)
        if current.count > 100 {
            current = Array(current.prefix(100))
        }
        UserDefaults.standard.set(current, forKey: logsKey)
    }

    public func install(sharedContext: SharedAccountContext) {
        let subscribeCurrent = { [weak self, weak sharedContext] in
            guard let self, let sharedContext else { return }
            let ids = self.trackedPeers.map { EnginePeer.Id($0) }
            guard !ids.isEmpty else {
                self.disposable.set(nil)
                return
            }
            let sig = sharedContext.activeAccountContexts
            |> mapToSignal { primary, _, _ -> Signal<(AccountContext, [EnginePeer.Id: EnginePeer?], [EnginePeer.Id: EnginePeer.Presence?]), NoError> in
                guard let primary else { return .complete() }
                let peersMap = primary.engine.data.subscribe(EngineDataMap(ids.map(TelegramEngine.EngineData.Item.Peer.Peer.init(id:))))
                let presMap = primary.engine.data.subscribe(EngineDataMap(ids.map(TelegramEngine.EngineData.Item.Peer.Presence.init(id:))))
                return combineLatest(peersMap, presMap) |> map { (primary, $0, $1) }
            }
            |> deliverOnMainQueue
            self.disposable.set(sig.start(next: { [weak self] context, peers, presences in
                guard let self, !AyuDecoyMode.isActive else { return }
                let pdata = context.sharedContext.currentPresentationData.with { $0 }
                let ru = pdata.strings.baseLanguageCode.hasPrefix("ru")
                let now = Int32(Date().timeIntervalSince1970)
                let fmt = DateFormatter()
                fmt.dateFormat = "dd.MM HH:mm:ss"
                for (id, maybePres) in presences {
                    guard let presence = maybePres else { continue }
                    let (_, isOnline) = stringAndActivityForUserPresence(strings: pdata.strings, dateTimeFormat: pdata.dateTimeFormat, presence: presence, relativeTo: now)
                    let raw = id.toInt64()
                    if let previous = self.lastOnlineState[raw], previous != isOnline {
                        let name = peers[id]??.compactDisplayTitle ?? "ID \\(raw)"
                        let statusText = isOnline ? (ru ? "в сети" : "is online") : (ru ? "вышел(а) из сети" : "went offline")
                        let stamp = fmt.string(from: Date())
                        self.appendLog("[\\(stamp)] \\(name) — \\(statusText)")
                        self.deliverAlert(title: name, body: statusText, peerId: raw, accountId: context.account.id.int64)
                    }
                    self.lastOnlineState[raw] = isOnline
                }
            }))
        }

        subscribeCurrent()
        let _ = NotificationCenter.default.addObserver(forName: Self.didChangeNotification, object: nil, queue: .main) { _ in
            subscribeCurrent()
        }
        let _ = NotificationCenter.default.addObserver(forName: Notification.Name("Nowzen.PeerInputActivityObserved"), object: nil, queue: .main) { [weak self] note in
            guard let self, !AyuDecoyMode.isActive,
                  UserDefaults.standard.bool(forKey: "ayu.extra.notifyActivity"),
                  let info = note.userInfo,
                  let rawPeerId = info["peerId"] as? Int64,
                  let name = info["name"] as? String,
                  let action = info["action"] as? String else { return }
            let now = Date().timeIntervalSince1970
            if let last = self.lastActivityCooldown[rawPeerId], now - last < 15.0 {
                return
            }
            self.lastActivityCooldown[rawPeerId] = now
            self.deliverAlert(title: name, body: action, peerId: rawPeerId, accountId: 0)
        }
    }

    private func deliverAlert(title: String, body: String, peerId: Int64, accountId: Int64) {
        if UIApplication.shared.applicationState == .active {
            AyuToast.shared.show("\\(title) · \\(body)")
        } else {
            let content = UNMutableNotificationContent()
            content.title = title
            content.body = body
            content.sound = .default
            if accountId != 0 {
                content.userInfo = ["accountId": accountId, "peerId": peerId]
            }
            UNUserNotificationCenter.current().add(UNNotificationRequest(identifier: "nowzen_trk_\\(peerId)_\\(Int(Date().timeIntervalSince1970))", content: content, trigger: nil), withCompletionHandler: nil)
        }
    }
}""",
        "nowzen_online_tracker_and_activity_notifier",
    )

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


def _enhance_profile_items(src: Path) -> None:
    prof_path = src / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"
    _replace_once(
        prof_path,
        """                    let history = AyuNameHistory.entries(noteValue)""",
        """                    items[currentPeerInfoSection]!.append(PeerInfoScreenActionItem(id: 9064, text: ru ? "Первое сообщение в чате" : "First message in chat", color: .accent, action: {
                        guard let nav = interaction.getController()?.navigationController as? NavigationController else { return }
                        let firstId = EngineMessage.Id(peerId: user.id, namespace: Namespaces.Message.Cloud, id: 1)
                        context.sharedContext.navigateToChatController(NavigateToChatControllerParams(navigationController: nav, context: context, chatLocation: .peer(EnginePeer.user(user)), subject: .message(id: .id(firstId), highlight: ChatControllerSubject.MessageHighlight(quote: nil), timecode: nil, setupReply: false)))
                    }))
                    items[currentPeerInfoSection]!.append(PeerInfoScreenActionItem(id: 9065, text: ru ? "Удалённые сообщения в чате" : "Deleted messages in chat", color: .accent, action: {
                        let _ = (context.engine.messages.ayuMessageHistory() |> take(1) |> deliverOnMainQueue).startStandalone(next: { state in
                            let recs = state.records.filter { $0.peerId == noteValue }
                            let title = ru ? "Удалённые и изменённые" : "Deleted & Edited"
                            let body: String
                            if recs.isEmpty {
                                body = ru ? "В этом чате пока нет сохранённых удалённых или изменённых сообщений." : "No saved deleted or edited messages in this chat."
                            } else {
                                let fmt = DateFormatter()
                                fmt.dateStyle = .short
                                fmt.timeStyle = .short
                                body = recs.suffix(25).reversed().map { r in
                                    let kind = r.kind == .deleted ? (ru ? "Удалено" : "Deleted") : (ru ? "Изменено" : "Edited")
                                    let txt = r.text.isEmpty ? (ru ? "[Медиа]" : "[Media]") : String(r.text.prefix(140))
                                    return "[\\(fmt.string(from: Date(timeIntervalSince1970: TimeInterval(r.recordedAt))))] \\(kind): \\(txt)"
                                }.joined(separator: "\\n\\n")
                            }
                            let alert = UIAlertController(title: title, message: body, preferredStyle: .alert)
                            alert.addAction(UIAlertAction(title: "OK", style: .default))
                            context.sharedContext.applicationBindings.presentNativeController(alert)
                        })
                    }))
                    let isTrackedPeer = ((UserDefaults.standard.array(forKey: "nowzen.tracker.peers") as? [NSNumber]) ?? []).map(\\.int64Value).contains(noteValue)
                    items[currentPeerInfoSection]!.append(PeerInfoScreenActionItem(id: 9066, text: isTrackedPeer ? (ru ? "Отслеживание входа/выхода: Вкл." : "Online tracker: On") : (ru ? "Отслеживать вход и выход в сеть" : "Track online/offline status"), color: .accent, action: {
                        var set = Set(((UserDefaults.standard.array(forKey: "nowzen.tracker.peers") as? [NSNumber]) ?? []).map(\\.int64Value))
                        let nowOn: Bool
                        if set.contains(noteValue) {
                            set.remove(noteValue)
                            nowOn = false
                        } else {
                            set.insert(noteValue)
                            nowOn = true
                        }
                        UserDefaults.standard.set(Array(set).sorted().map { NSNumber(value: $0) }, forKey: "nowzen.tracker.peers")
                        NotificationCenter.default.post(name: Notification.Name("Nowzen.OnlineTrackerChanged"), object: nil)
                        let msg = nowOn
                            ? (ru ? "Уведомления о входе и выходе этого пользователя включены." : "Online/offline notifications enabled for this user.")
                            : (ru ? "Отслеживание для этого пользователя отключено." : "Online tracking disabled for this user.")
                        let alert = UIAlertController(title: ru ? "Отслеживание контакта" : "Contact Tracker", message: msg, preferredStyle: .alert)
                        alert.addAction(UIAlertAction(title: "OK", style: .default))
                        context.sharedContext.applicationBindings.presentNativeController(alert)
                    }))
                    let history = AyuNameHistory.entries(noteValue)""",
        "profile_first_message_deleted_and_tracker_buttons",
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
            ("VoidGram · MessageShot" as NSString).draw(at: CGPoint(x: 28.0, y: 28.0), withAttributes: [.font: UIFont.systemFont(ofSize: 30.0, weight: .semibold), .foregroundColor: secondary])
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
    let background = dark ? UIColor(rgb: 0x121317) : UIColor(rgb: 0xECEEF2)
    let secondary = dark ? UIColor(white: 0.72, alpha: 0.85) : UIColor(white: 0.40, alpha: 0.9)
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
                ? (card.outgoing ? UIColor(rgb: 0x2A2D37) : UIColor(rgb: 0x1B1D24))
                : (card.outgoing ? UIColor(rgb: 0xE2E5EC) : .white)
            fill.setFill()
            UIBezierPath(roundedRect: frame, cornerRadius: 22.0).fill()
            if showAuthors {
                let authorColor = dark ? UIColor(rgb: 0xD4D8E2) : UIColor(rgb: 0x2A2D37)
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
    extras_path = src / "submodules/SettingsUI/Sources/AyuExtrasController.swift"
    _replace_once(
        extras_path,
        """        let undoSeconds = UserDefaults.standard.integer(forKey: "ayu.extra.undoSendSeconds")
        entries.append(.link(4, 35, AyuSettingsIcons.symbol("arrow.uturn.backward.circle.fill", color: UIColor(rgb: 0x34C759)), ru ? "Отмена отправки" : "Undo send", undoSeconds == 0 ? (ru ? "выкл." : "off") : (ru ? "\\(undoSeconds) с" : "\\(undoSeconds) s")))
        if AyuFeatureGate.isUnlocked {
            entries.append(.link(4, 36, AyuSettingsIcons.symbol("trash.fill", color: UIColor(rgb: 0xFF3B30)), ru ? "Очистить сохранённые удалённые" : "Clear saved deleted", ""))
            entries.append(.link(4, 37, AyuSettingsIcons.symbol("eraser.fill", color: UIColor(rgb: 0xFF9500)), ru ? "Очистить сохранённые изменённые" : "Clear saved edits", ""))
            entries.append(.link(4, 38, AyuSettingsIcons.symbol("square.and.arrow.up.fill", color: UIColor(rgb: 0x007AFF)), ru ? "Экспорт удалённых и изменённых" : "Export deleted and edited", "JSON"))
            entries.append(.link(4, 39, AyuSettingsIcons.symbol("list.bullet.rectangle.portrait.fill", color: UIColor(rgb: 0xAF52DE)), ru ? "Лента удалённых и изменённых" : "Deleted and edited feed", ru ? "поиск" : "search"))
        }""",
        """        if AyuFeatureGate.isUnlocked {
            entries.append(.link(4, 36, AyuSettingsIcons.symbol("trash.fill", color: UIColor(rgb: 0x8E8E93)), ru ? "Очистить сохранённые удалённые" : "Clear saved deleted", ""))
            entries.append(.link(4, 37, AyuSettingsIcons.symbol("eraser.fill", color: UIColor(rgb: 0x8E8E93)), ru ? "Очистить сохранённые изменённые" : "Clear saved edits", ""))
            entries.append(.link(4, 38, AyuSettingsIcons.symbol("square.and.arrow.up.fill", color: UIColor(rgb: 0x8E8E93)), ru ? "Экспорт удалённых и изменённых" : "Export deleted and edited", "JSON"))
            entries.append(.link(4, 39, AyuSettingsIcons.symbol("list.bullet.rectangle.portrait.fill", color: UIColor(rgb: 0x8E8E93)), ru ? "Лента удалённых и изменённых" : "Deleted and edited feed", ru ? "поиск" : "search"))
        }
        let undoSeconds = UserDefaults.standard.integer(forKey: "ayu.extra.undoSendSeconds")
        entries.append(.link(4, 40, AyuSettingsIcons.symbol("arrow.uturn.backward.circle.fill", color: UIColor(rgb: 0x8E8E93)), ru ? "Отмена отправки" : "Undo send", undoSeconds == 0 ? (ru ? "выкл." : "off") : (ru ? "\\(undoSeconds) с" : "\\(undoSeconds) s")))
        entries.append(.header(5, 50, ru ? "ОТСЛЕЖИВАНИЕ И АКТИВНОСТЬ" : "TRACKING & ACTIVITY"))
        let notifyAct = UserDefaults.standard.bool(forKey: "ayu.extra.notifyActivity")
        entries.append(.toggle(5, 51, AyuSettingsIcons.symbol("waveform.badge.exclamationmark", color: UIColor(rgb: 0x8E8E93)), ru ? "Уведомлять об активности (печатает/записывает)" : "Notify on chat activity (typing/recording)", ru ? "Показывать уведомление, когда собеседник печатает или записывает голосовое/кружок" : "Alert when someone types or records voice/video", notifyAct))
        let trackedCount = ((UserDefaults.standard.array(forKey: "nowzen.tracker.peers") as? [NSNumber]) ?? []).count
        entries.append(.link(5, 52, AyuSettingsIcons.symbol("person.wave.2.fill", color: UIColor(rgb: 0x8E8E93)), ru ? "Отслеживание контактов (вход/выход)" : "Contact online tracker", trackedCount > 0 ? "\\(trackedCount)" : ""))
        entries.sort()""",
        "fix_extras_duplicate_id_35_and_add_tracker_rows",
    )
    _replace_once(
        extras_path,
        """        if id == 35 {""",
        """        if id == 52 {
            let logs = UserDefaults.standard.stringArray(forKey: "nowzen.tracker.logs") ?? []
            let tracked = ((UserDefaults.standard.array(forKey: "nowzen.tracker.peers") as? [NSNumber]) ?? []).count
            let header = ru ? "Отслеживается людей: \\(tracked)\\n(Включить отслеживание можно в профиле любого пользователя)" : "Tracked users: \\(tracked)\\n(Toggle tracking in any user's profile)"
            let body = logs.isEmpty ? (ru ? "\\nПока нет зафиксированных входов или выходов." : "\\nNo online/offline events recorded yet.") : ("\\n\\n" + logs.prefix(30).joined(separator: "\\n"))
            let alert = UIAlertController(title: ru ? "Журнал входов и выходов" : "Online/Offline Log", message: header + body, preferredStyle: .alert)
            if !logs.isEmpty {
                alert.addAction(UIAlertAction(title: ru ? "Очистить журнал" : "Clear log", style: .destructive, handler: { _ in
                    UserDefaults.standard.removeObject(forKey: "nowzen.tracker.logs")
                }))
            }
            alert.addAction(UIAlertAction(title: "OK", style: .default))
            context.sharedContext.applicationBindings.presentNativeController(alert)
            return
        }
        if id == 40 {""",
        "fix_extras_duplicate_id_35_handler_and_tracker_log",
    )
    _replace_once(
        extras_path,
        """    }, toggle: { id, value in
        guard let row = ayuExtraRows.first(where: { $0.id == id }) else { return }
        AyuExtras.set(row.key, value)
    })""",
        """    }, toggle: { id, value in
        if id == 51 {
            UserDefaults.standard.set(value, forKey: "ayu.extra.notifyActivity")
            NotificationCenter.default.post(name: AyuExtras.didChangeNotification, object: nil)
            return
        }
        guard let row = ayuExtraRows.first(where: { $0.id == id }) else { return }
        AyuExtras.set(row.key, value)
    })""",
        "extras_toggle_notify_activity",
    )

    cat_path = src / "submodules/SettingsUI/Sources/AyuCategoriesController.swift"
    _replace_once(
        cat_path,
        """    case .privacy:
        return [
            AyuCategoryItem(id: 1, symbol: "eye.slash.fill", color: 0x8E5CF7, titleRu: "Режим призрака", titleEn: "Ghost Mode", subtitleRu: "Прочтения, онлайн, набор, загрузка", subtitleEn: "Read receipts, online, typing, uploads", open: page { ayuGhostModeController(context: $0) }, ghostPlus: false),
            AyuCategoryItem(id: 2, symbol: "eye.trianglebadge.exclamationmark.fill", color: 0x5856D6, titleRu: "Режим призрака+", titleEn: "Ghost Mode+", subtitleRu: "Тонкая настройка", subtitleEn: "Fine-tuning", open: page { ayuGhostModePlusController(context: $0) }, ghostPlus: true),
            AyuCategoryItem(id: 3, symbol: "person.crop.circle.badge.checkmark", color: 0x8E5CF7, titleRu: "Призрак по чатам", titleEn: "Ghost Mode by chat", subtitleRu: "Включить или выключить в отдельных чатах", subtitleEn: "On or off in single chats", open: page { ayuGhostExceptionsController(context: $0) }),
            AyuCategoryItem(id: 4, symbol: "figure.walk.motion", color: 0x34C759, titleRu: "Активность и следы", titleEn: "Activity & traces", subtitleRu: "Статусы, всегда онлайн, прочитать локально, истории, номер", subtitleEn: "Statuses, always online, read locally, stories, number", open: page { ayuPrivacyPlusController(context: $0) }),
            AyuCategoryItem(id: 5, symbol: "hand.raised.fill", color: 0x34C759, titleRu: "Приватность и мелочи", titleEn: "Privacy & extras", subtitleRu: "Метаданные фото, чистые ссылки, анти-скам, звонки", subtitleEn: "Photo metadata, clean links, anti-scam, calls", open: page { ayuExtrasController(context: $0) }),
            AyuCategoryItem(id: 6, symbol: "trash.fill", color: 0xFF3B30, titleRu: "Удалённые", titleEn: "Deleted", subtitleRu: "Как видно в чате, прозрачность, иконка, уведомления", subtitleEn: "How they look, transparency, icon, notifications", open: page { ayuDeletedMessagesController(context: $0) })
        ]""",
        """    case .privacy:
        return [
            AyuCategoryItem(id: 1, symbol: "eye.slash.fill", color: 0x262932, titleRu: "Режим призрака", titleEn: "Ghost Mode", subtitleRu: "Прочтения, онлайн, набор, анонимные истории", subtitleEn: "Read receipts, online, typing, anonymous stories", open: page { ayuGhostModeController(context: $0) }, ghostPlus: false),
            AyuCategoryItem(id: 2, symbol: "eye.trianglebadge.exclamationmark.fill", color: 0x262932, titleRu: "Тонкая настройка призрака", titleEn: "Ghost Mode+", subtitleRu: "Доп. параметры скрытности", subtitleEn: "Fine-tuning", open: page { ayuGhostModePlusController(context: $0) }, ghostPlus: true),
            AyuCategoryItem(id: 3, symbol: "person.crop.circle.badge.checkmark", color: 0x262932, titleRu: "Призрак по чатам", titleEn: "Ghost Mode by chat", subtitleRu: "Исключения для отдельных чатов", subtitleEn: "On or off in single chats", open: page { ayuGhostExceptionsController(context: $0) }),
            AyuCategoryItem(id: 4, symbol: "figure.walk.motion", color: 0x262932, titleRu: "Активность и следы", titleEn: "Activity & traces", subtitleRu: "Статусы, всегда онлайн, истории, номер", subtitleEn: "Statuses, always online, read locally, stories, number", open: page { ayuPrivacyPlusController(context: $0) }),
            AyuCategoryItem(id: 6, symbol: "trash.fill", color: 0x262932, titleRu: "Отображение удалённых", titleEn: "Deleted", subtitleRu: "Полупрозрачность, метки и уведомления", subtitleEn: "Transparency, marks and notifications", open: page { ayuDeletedMessagesController(context: $0) }),
            AyuCategoryItem(id: 5, symbol: "bell.and.waves.left.and.right.fill", color: 0x262932, titleRu: "Слежка, активность и мелочи", titleEn: "Tracker, activity & extras", subtitleRu: "Онлайн-трекер людей, уведомления о печати, ссылки", subtitleEn: "Online tracker, typing alerts, metadata, links", open: page { ayuExtrasController(context: $0) })
        ]""",
        "reorganize_privacy_category_items",
    )
    _replace_once(
        cat_path,
        """    case .security:
        return [
            AyuCategoryItem(id: 51, symbol: "lock.fill", color: 0xFF9500, titleRu: "Защита чатов", titleEn: "Chat protection", subtitleRu: "Face ID на чаты, скрытые чаты, скриншоты", subtitleEn: "Face ID chats, hidden chats, screenshots", open: page { ayuChatProtectionController(context: $0) }),
            AyuCategoryItem(id: 52, symbol: "theatermasks.fill", color: 0x5856D6, titleRu: "Режим-приманка и двойное дно", titleEn: "Decoy & hidden account", subtitleRu: "Второй аккаунт за отдельным кодом", subtitleEn: "A second account behind its own code", open: page { ayuDecoySettingsController(context: $0) }),
            AyuCategoryItem(id: 53, symbol: "person.2.fill", color: 0x007AFF, titleRu: "Аккаунты", titleEn: "Accounts", subtitleRu: "Настройки VoidGram для каждого аккаунта", subtitleEn: "VoidGram settings per account", open: page { ayuAccountsSettingsController(context: $0) })
        ]""",
        """    case .security:
        return [
            AyuCategoryItem(id: 51, symbol: "lock.shield.fill", color: 0x262932, titleRu: "Защита чатов и Face ID", titleEn: "Chat protection", subtitleRu: "Блокировка чатов Face ID, скрытые чаты", subtitleEn: "Face ID chats, hidden chats, screenshots", open: page { ayuChatProtectionController(context: $0) }),
            AyuCategoryItem(id: 52, symbol: "theatermasks.fill", color: 0x262932, titleRu: "Чистый Telegram (приманка)", titleEn: "Decoy & hidden account", subtitleRu: "Скрыть моды или открыть второй аккаунт", subtitleEn: "Hide mods or use second account", open: page { ayuDecoySettingsController(context: $0) }),
            AyuCategoryItem(id: 53, symbol: "person.2.fill", color: 0x262932, titleRu: "Аккаунты", titleEn: "Accounts", subtitleRu: "Отдельные настройки Nowzen по аккаунтам", subtitleEn: "Nowzen settings per account", open: page { ayuAccountsSettingsController(context: $0) })
        ]""",
        "reorganize_security_category_items",
    )


def apply_nowzen_enhancements(src: Path) -> None:
    _enhance_graphite_theme_and_welcome(src)
    _enhance_app_delegate(src)
    _enhance_app_extras_defaults(src)
    _enhance_chat_privacy_and_face_id(src)
    _enhance_ghost_mode_stories_and_chat_buttons(src)
    _enhance_compact_chat_list_and_activity_hook(src)
    _enhance_deleted_and_view_once_media(src)
    _enhance_tracker_notifications_and_context_menu(src)
    _enhance_profile_items(src)
    _enhance_message_shot_native_look(src)
    _enhance_settings_stability_and_grouping(src)
