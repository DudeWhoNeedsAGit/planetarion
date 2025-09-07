milestone: "Global Chat MVP"

description: |
  Implement a global chat system to amplify player engagement and social drama.
  The chat should be integrated into the main game UI, tied to authentication,
  and support both player messages and system event broadcasts (e.g. raids, discoveries).
  Focus on simplicity, persistence, and fast dopamine feedback for a small group (5–10 players).

tasks:
  - name: "Backend: Chat Message Model & API"
    description: |
      - Create a `chat_messages` table (id, user_id, username, message, timestamp).
      - Add backend API endpoints:
        - `GET /chat/messages` → fetch last N messages (with pagination).
        - `POST /chat/messages` → add new message (requires JWT auth).
      - Add server-side validation (max length, strip HTML, basic profanity filter optional).
      - Enforce basic rate limiting (e.g. max 5 messages per 10s per user).
    acceptance_criteria: |
      - Messages are persisted in DB.
      - Authenticated users can send/fetch messages.
      - Invalid/oversized/spam messages are rejected.

  - name: "Frontend: Chat UI Panel"
    description: |
      - Create a chat panel docked to the right or bottom of the game screen.
      - Display last ~50 messages, auto-scroll to newest.
      - Input box at bottom, send button or enter-to-send.
      - Messages should show username + timestamp + text.
      - Implement basic styling (distinct player colors, small font).
      - Add toggle/minimize button so chat can be hidden.
    acceptance_criteria: |
      - Players can open chat, see recent messages, send new ones.
      - New messages appear without full page reload (via polling every 5s or websocket if infra allows).
      - UI is non-intrusive but always accessible.

  - name: "System Message Integration"
    description: |
      - Hook into existing PvP/raid events and exploration (future) to generate system messages.
      - Example: "🚀 PlayerX raided PlayerY and stole 120 Metal" or "🌌 Comet discovered at [3:45:12]".
      - System messages stored in same table with a `system` flag and special styling.
    acceptance_criteria: |
      - System events automatically appear in chat in real time.
      - System messages visually distinct (different color/icon).
      - Players cannot forge system messages.

  - name: "Testing & Polish"
    description: |
      - Verify chat works across multiple browsers/users simultaneously.
      - Stress test with 5–10 users spamming to ensure no crashes.
      - Ensure timestamps use player’s local timezone or UTC consistently.
      - UI scaling works on both desktop and mobile browser.
    acceptance_criteria: |
      - No duplicate or missing messages under normal usage.
      - System and user messages coexist cleanly.
      - Chat remains responsive even under rapid use.

priority: "high"
