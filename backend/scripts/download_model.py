from app.services.embeddings import get_embedder

if __name__ == "__main__":
    emb = get_embedder()
    vec = emb.embed_text("warm-up sentence")
    print(f"Model ready. Embedding dimension = {vec.shape[0]}")