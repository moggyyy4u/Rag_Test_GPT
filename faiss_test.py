from sentence_transformers import SentenceTransformer
import faiss

model = SentenceTransformer("all-MiniLM-L6-v2")


sentences = [
    "Two-phase locking is a database concurrency control protocol.",
    "2PL is used to control concurrent transactions in a database.",
    "The weather is sunny and I went outside."
]


vectors = model.encode(sentences)


dimension = vectors.shape[1]

index = faiss.IndexFlatL2(dimension)


index.add(vectors)

question = "What is 2PL used for?"


question_vector = model.encode([question])


distances, indices = index.search(question_vector, 2)

print("Distances:")
print(distances)

print("Indices:")
print(indices)


for i in indices[0]:
    print(sentences[i])