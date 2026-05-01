import numpy as np
import pickle
import os

class SimpleVectorStore:
    def __init__(self, storage_path="vector_store.pkl"):
        self.storage_path = storage_path
        self.embeddings = []
        self.documents = []
        self.metadatas = []
        self.ids = []
        self.load()

    def add(self, documents, embeddings, metadatas=None, ids=None):
        self.documents.extend(documents)
        self.embeddings.extend(embeddings)
        if metadatas: self.metadatas.extend(metadatas)
        if ids: self.ids.extend(ids)
        self.save()

    def save(self):
        data = {
            "embeddings": np.array(self.embeddings, dtype=np.float32),
            "documents": self.documents,
            "metadatas": self.metadatas,
            "ids": self.ids
        }
        with open(self.storage_path, "wb") as f:
            pickle.dump(data, f)

    def load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "rb") as f:
                    data = pickle.load(f)
                    self.embeddings = list(data["embeddings"])
                    self.documents = data["documents"]
                    self.metadatas = data["metadatas"]
                    self.ids = data["ids"]
            except:
                pass

    def query(self, query_embeddings, n_results=3):
        if not self.embeddings:
            return {"documents": [[]], "distances": [[]], "metadatas": [[]]}
        
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        # Convert query and store to numpy for fast math
        q = np.array(query_embeddings[0]).reshape(1, -1)
        store = np.array(self.embeddings)
        
        # Calculate Cosine Similarity
        # Higher score means more similar (0 to 1)
        scores = cosine_similarity(q, store)[0]
        
        # Get top N indices (sorted by highest similarity score)
        indices = np.argsort(scores)[::-1][:n_results]
        
        # Convert similarity to a "distance" metric (1 - score) for consistency with threshold logic
        # Distance 0 means identical, Distance 1 means completely different
        return {
            "documents": [[self.documents[i] for i in indices]],
            "distances": [[float(1 - scores[i]) for i in indices]],
            "metadatas": [[self.metadatas[i] for i in indices] if self.metadatas else [None for _ in indices]]
        }

    def count(self):
        return len(self.documents)
