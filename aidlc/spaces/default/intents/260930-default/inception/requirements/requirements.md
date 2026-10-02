# Requirements Document

## Intent Analysis Summary
- **User Request**: Implement the UI (Flet) and Cloud Sync (Supabase), focusing initially on the UI module.
- **Request Type**: New Feature
- **Scope Estimate**: Multiple Components (UI, Engine bindings, Cloud storage)
- **Complexity Estimate**: Complex (Involves realtime STT, neural net inference, async updates, animated waveforms, and property-based testing enforcement)

## Functional Requirements
1. **Fully Responsive Flet UI**: The application must have a unified, responsive interface that adapts to Desktop, Web, and Mobile layouts, featuring a Sci-Fi aesthetic (Neon Cyan and Orange on dark backgrounds).
2. **Dynamic Animated Waveform**: The UI must display an animated waveform component in the Learning Module reacting to microphone capture in real-time, moving beyond a static image.
3. **Mocked Supabase Sync Logic**: A mock implementation of the Supabase Sync logic (Push/Pull) must be created using the `synced` and `updated_at` properties, functioning locally without requiring a live Supabase URL/Key initially.
4. **Offline First Architecture**: The system must operate perfectly offline for real-time translation and only sync when commanded.
5. **Missing Words System**: The Conversation Module must parse transcribed STT text against the vector dictionary and visually alert the user (red text) for unrecognized tokens.

## Non-Functional Requirements
1. **Security**: Must adhere strictly to the Security Baseline Extension rules (enforced as blocking constraints). No hardcoded secrets, mandatory input validation, and secure handling of local SQLite queries.
2. **Resiliency**: Must follow the Resiliency Baseline Extension rules (AWS Well-Architected Framework). Fallbacks for STT failures, robust handling of microphone disconnections, and graceful degradation for cloud sync mock errors.
3. **Property-Based Testing (PBT)**: Complex logic (e.g., STT text splitting, vector gap detection, mock syncing data structures) must be tested using Property-Based Testing to verify invariants across a wide range of fuzz inputs.
4. **Performance**: Real-time STT rendering and visual animations must not block the main thread. Audio processing loops must remain asynchronous.

## Key Decisions
- **Flet Framework**: Chosen for its capacity to run natively on Desktop/Web/Mobile with a Python backend.
- **Mock First Approach**: Instead of wrestling with immediate cloud infra setup, the Cloud Sync logic will be mocked to validate the architecture and UUID implementation.
