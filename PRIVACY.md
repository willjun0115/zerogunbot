# Privacy Policy for ZeroGunBot

Last updated: September 15, 2026

ZeroGunBot ("the Bot") is a Discord bot designed to provide server management utilities, minigames, audio playback, and gaming statistics search. This Privacy Policy explains how data is collected, stored, processed, and protected when you interact with the Bot.

By adding ZeroGunBot to your server or interacting with its features, you agree to the terms described in this Privacy Policy.

---

## 1. Information We Collect

When using ZeroGunBot, the following information may be accessed and processed:

1. **Discord Identifiers (Stored)**:
   - **User ID**: Stored in a local SQLite database to track in-bot virtual currency (tokens), minigame progress, luck stats, and custom abilities.
   - **Guild (Server) ID & Channel ID**: Stored or cached temporarily to handle server-specific commands, permissions, and log routing.

2. **Temporary Operational Data (Not Stored Permanently)**:
   - **Message Content**: Processed only when a command with prefix `%` or `@mention` is triggered, solely to parse arguments and execute the requested command. Messages are not logged, archived, or stored permanently.
   - **Voice Connection State**: Processed in real-time to connect, play audio, and disconnect from voice channels.
   - **External Gaming Queries (e.g., Riot ID)**: Temporarily processed in memory to fetch public statistics from the Riot Games API upon user request.

---

## 2. How We Use Your Information

The collected data is strictly used for the following purposes:
- Delivering core bot functionality (e.g., balance lookup, minigames, music playback, stats search).
- Enforcing cooldowns, permissions, and rate limits to prevent abuse and spam.
- Maintaining bot system stability and performance.

We do **NOT** use your data for advertising, profiling, or tracking across other services.

---

## 3. Data Storage and Security

- **Storage Location**: Stored securely on private, self-hosted server storage running the bot.
- **Third-Party Sharing**: We do **NOT** sell, rent, lease, or share any collected user data with any third parties or commercial entities.
- **Retention Period**: Data associated with a user's bot account is retained until the user requests data deletion or the bot's database is reset.

---

## 4. User Rights and Data Deletion

In compliance with Discord's Developer Policy, users have the right to request access to or deletion of their stored data at any time:

- **How to Request Deletion**: You can request full deletion of your user record and token history by:
  1. Creating an issue on the official GitHub repository: [https://github.com/willjun0115/zerogunbot/issues](https://github.com/willjun0115/zerogunbot/issues)
  2. Contacting the bot owner directly on Discord.
- Once requested, all associated records in the database will be permanently removed within 7 business days.

---

## 5. Compliance with Discord Developer Terms

ZeroGunBot operates in full compliance with the [Discord Developer Terms of Service](https://discord.com/developers/docs/policies-and-agreements/developer-terms-of-service) and [Discord Community Guidelines](https://discord.com/guidelines).

---

## 6. Children's Privacy (COPPA)

ZeroGunBot is not directed towards children under the age of 13 (or the minimum age of digital consent in your jurisdiction). In accordance with Discord's Terms of Service, users under Discord's minimum required age are prohibited from using the Bot.

---

## 7. Contact Us

If you have questions, feedback, or data privacy requests regarding ZeroGunBot, please open an issue or discussion on GitHub:
- **Repository**: [https://github.com/willjun0115/zerogunbot](https://github.com/willjun0115/zerogunbot)

