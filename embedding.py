from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

model = SentenceTransformer("all-MiniLM-L6-v2")

sentences = [
    "Two-phase locking is a database concurrency control protocol.",
    "2PL is used to control concurrent transactions in a database.",
    "The weather is sunny and I went outside."
]

vectors = model.encode(sentences)
similarity = cos_sim(vectors, vectors)

print(similarity)

#print(vectors.shape)