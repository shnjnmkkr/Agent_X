import faiss
import numpy as np
from typing import List, Dict, Tuple
import pickle
import os
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.stored_data: List[Dict] = []
        self.dimension = 384  # Default for MiniLM

    def create_index(self, texts: List[str], metadata: List[Dict] = None):
        """Create FAISS index from texts"""
        try:
            embeddings = self.model.encode(texts)
            self.index = faiss.IndexFlatL2(self.dimension)
            self.index.add(np.array(embeddings).astype('float32'))
            
            # Store metadata
            if metadata:
                self.stored_data = metadata
            else:
                self.stored_data = [{"text": text} for text in texts]
                
            logger.info(f"Created index with {len(texts)} vectors")
            
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            raise

    def search(self, query: str, k: int = 5) -> List[Dict]:
        """Search for similar vectors"""
        try:
            query_vector = self.model.encode([query])
            distances, indices = self.index.search(
                np.array(query_vector).astype('float32'), k
            )
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.stored_data):
                    result = self.stored_data[idx].copy()
                    result['distance'] = float(distances[0][i])
                    results.append(result)
                    
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []

    def save(self, path: str):
        """Save index and data to disk"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            faiss.write_index(self.index, f"{path}.index")
            with open(f"{path}.pkl", 'wb') as f:
                pickle.dump(self.stored_data, f)
            logger.info(f"Saved index to {path}")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise

    def load(self, path: str):
        """Load index and data from disk"""
        try:
            self.index = faiss.read_index(f"{path}.index")
            with open(f"{path}.pkl", 'rb') as f:
                self.stored_data = pickle.load(f)
            logger.info(f"Loaded index from {path}")
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            raise 