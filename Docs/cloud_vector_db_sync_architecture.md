# Cloud Vector Database & Interstellar Sync Architecture

This document outlines the theoretical architecture for migrating our local vector embeddings to the cloud and establishing a synchronization mechanism suitable for interstellar exploration scenarios, as inspired by *Project Hail Mary*.

## 1. Cloud Vector Database Analysis

To centralize the dictionary/vocabulary (currently stored locally via ChromaDB), we analyzed two major cloud solutions that offer free tiers suitable for our current scale:

### Qdrant Cloud
*   **Overview:** A dedicated, high-performance vector search engine.
*   **Free Tier:** 1GB RAM / 4GB storage (can store ~250,000 vectors of 1024D).
*   **Pros:** Native support for advanced filtering, ultra-fast vector search capabilities, specialized purely for embeddings.
*   **Cons:** Requires maintaining two separate databases if we keep SQLite for relational metadata.

### Supabase (pgvector)
*   **Overview:** An open-source Firebase alternative built on top of PostgreSQL, utilizing the `pgvector` extension for embeddings.
*   **Free Tier:** 500MB database space.
*   **Pros:** Allows us to unify our relational data (currently in SQLite) and our vector data (currently in ChromaDB) into a single, cohesive PostgreSQL database.
*   **Cons:** Vector search performance is slightly less optimized out-of-the-box compared to a dedicated engine like Qdrant, though entirely sufficient for our scale.

**Recommendation:** **Supabase** is the recommended choice for this project. The ability to unify our `Registry` (metadata) and `VectorDB` (embeddings) into a single PostgreSQL instance dramatically simplifies the architecture and deployment.

---

## 2. Interstellar Synchronization Architecture (The "Hail Mary" Sync)

**The Scenario:** Astronauts (like Ryland Grace) or field researchers venture out of communication range, interact with new species (like Rocky), learn new vocabulary offline, and later need to synchronize this knowledge base with Earth or other ships upon re-entering communication range.

### Local-First with Asynchronous Sync

To support this, the architecture must be **Local-First**:
1.  **Offline Autonomy:** The spacecraft (local machine) runs a full instance of the Universal Translator. It has a local SQLite/ChromaDB replica (or a local PostgreSQL instance). All translation, audio processing, and Siamese Network inferences run 100% offline.
2.  **Learning on the Fly:** When the astronaut learns a new alien word, it is recorded locally. The local database acts as the immediate source of truth, logging the entry with a timestamp and a `mission_id` / `author_id`.

### The Sync Mechanism

When the spacecraft establishes a connection with the central cloud (Supabase), the sync process begins:

1.  **Push (Upstream):** 
    *   The local system queries its database for all records (audio embeddings + metadata) created *after* the last successful sync timestamp.
    *   These new records are pushed to the Supabase cloud instance via an API or direct connection.
2.  **Pull (Downstream):**
    *   The local system queries Supabase for any new vocabulary entries added by *other* missions or researchers since its last sync.
    *   These records are downloaded and inserted into the local database, instantly expanding the local dictionary.
3.  **Conflict Resolution:**
    *   Given the nature of a dictionary, most operations are additive (inserting new words).
    *   If two missions map the same concept differently, the system does not overwrite; it appends both versions with their respective `author_id` and confidence scores. This allows the Siamese network to use both as positive/negative examples in future local fine-tuning.

### 🛠️ The 3 Technical Pillars to Make This Work

To implement this idea in the future without conflicts, we need to adjust three key things in our data modeling:

1. **Global Unique Identification (UUID)**
   *   *Currently:* The local SQLite database uses simple sequential primary keys (id = 1, 2, 3...).
   *   *The Problem:* If you register the word "HUNGER" in space (as ID 5) and a scientist on Earth registers the word "WATER" (also as ID 5), there will be a catastrophic collision during synchronization.
   *   *The Solution:* Change the identifier to a UUID (e.g., `d3b07384-d113-4956-a53e-5612f00b4632`). Each registered word gets a unique universal identifier based on a hash, ensuring zero collisions across planets.

2. **Local State Control (Flags)**
   *   We will add two simple columns to the `dictionary` table in SQLite:
       *   `synced` (boolean): `0` for words learned locally in space that haven't been pushed yet; `1` for words already synchronized with the cloud.
       *   `updated_at` (timestamp): to track exactly which version of the word is the most recent.

3. **Physical File Storage (.wav)**
   *   Vector databases save mathematical coordinates (the 1024D vectors), but they do not store the actual audio files.
   *   To sync the actual audios, we need a Cloud Object Storage (like a Supabase Storage bucket or AWS S3).
   *   *On Sync (Push):* The system grabs local `.wav` files where `synced = 0`, uploads them to the cloud bucket, and pushes the metadata + vectors to the cloud database.
   *   *On Sync (Pull):* The system queries the cloud database for records created after its last sync time, downloads the corresponding new `.wav` files into the local folder, and inserts the vector signatures into the local indexer.

---

### 🔄 The Practical Cycle on the Spaceship

*   **Before leaving Earth:** You run `scripts/sync_vocabulary.py --pull`. It downloads all humanity's contributions, places the audios in your folder, updates your local SQLite/Chroma, and triggers the Siamese network training. Your translator's "brain" is fully updated from Earth.
*   **During the mission (Totally Offline):** You interact with Rocky. Every new word he teaches you is saved locally with `synced = 0`.
*   **Upon re-establishing communication:** You run `scripts/sync_vocabulary.py --push`. The script scans the local SQLite, uploads Rocky's audios to the cloud, sends the new vectors to Supabase/Qdrant Cloud, and marks everything locally as `synced = 1`.
*   *From this moment on, all other scientists on Earth have immediate access to the "Rocky dialect" you discovered!*

### Future Implementation Paths
*   **Manual Sync Trigger:** A UI button in the planned Frontend (`[SYNC DATA]`) that manually initiates the push/pull script.
*   **Automated Sync:** Using tools like ElectricSQL or PowerSync, which natively handle bidirectional SQLite-to-Postgres synchronization with conflict resolution for local-first apps.
