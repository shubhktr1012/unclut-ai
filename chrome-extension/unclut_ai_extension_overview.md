# unclut.ai — Gmail Smart Inbox Cleaner (Browser Extension Version)

## 🧠 Vision
unclut.ai is a smart Gmail browser extension that helps users:
- **Unsubscribe** from promotional mailing lists
- **Delete emails** from specific senders
- **Clean their inbox** with minimal friction
- Use **AI summaries, suggestions, and tips** to make smart decisions

The extension is designed to be clean, helpful, habit-forming, and elegant — like a cross between **Notion’s minimal clarity** and **Arc’s delightful UX**.

---

## 🧩 Core MVP Interaction Model (Chosen: Option 1)

We’re starting with **inline interactions inside the Gmail inbox**:

- A **small icon** is injected next to the sender's name.
- On **hover**, it shows 3 buttons:
  - `Unsubscribe`
  - `Delete All`
  - `Unsubscribe + Delete`
- On clicking any, a **toast popup** appears at the bottom (like Gmail’s “Undo” snackbar), showing progress and offering an **Undo** option.

This is the MVP. More advanced features like **side panel**, **AI summaries**, and **daily cleaning tips** will be added later.

---

## 🛠️ Extension Tech Stack & Structure (Planned)

### 🔧 Files & Responsibilities
```
unclut-extension/
├── manifest.json               ← Manifest V3 config
├── background.js               ← OAuth & Gmail API calls
├── contentScript.js            ← DOM injection, UI triggers
├── gmailUtils.js               ← DOM parsing, sender detection
├── actions.js                  ← API logic (unsubscribe, delete)
├── ui.css                      ← Styling for popovers, toasts
├── icons/                      ← Small SVG/PNG for sender icon
└── popup.html (optional)       ← May be used for settings later
```

---

## ⚙️ Core Functionality To Build (Phase-wise)

### ✅ Phase 1: Inline UI + Logging
- Inject sender icon
- Show 3-button UI on hover
- Log sender email when buttons are clicked
- Show animated toast popup

### 🔜 Phase 2: Gmail API Integration
- Use OAuth2 to authenticate user
- `unsubscribeFromSender()`
- `deleteAllEmailsFromSender()`
- `unsubscribeAndDelete()`
- `undoLastAction()` (optional)

### 🔮 Future AI Features
- Confidence score per mailing list
- AI-generated gist of sender’s email history
- Stats: subscribed date, total mails, unread count
- Smart suggestions to clean up
- Daily AI tip on inbox hygiene

---

## 🔐 Permissions Required
- OAuth2 with `https://www.googleapis.com/auth/gmail.modify`
- Host permissions for Gmail domain
- Scripting permissions for injecting into Gmail inbox

---

## 🎨 UI Design Philosophy
- Clean, native-feeling Gmail integration
- Minimal popups, no clutter
- Actions feel fast, clear, and safe (with Undo)
- Builds user trust with thoughtful UX (progress, tooltips, animations)

---

## 🚀 Next Step: MVP Phase 1

- [ ] Inject icons next to each email sender in Gmail’s DOM
- [ ] On hover, show minimal box with 3 options
- [ ] Log sender email + selected action
- [ ] Display animated toast/snackbar popup at bottom