import joblib

# Load trained model
model = joblib.load("models/intent_model.pkl")

print("=" * 50)
print("AI Intent Detection Tester")
print("=" * 50)

while True:
    instruction = input("\nEnter instruction (type 'exit' to quit): ")

    if instruction.lower() == "exit":
        print("Exiting...")
        break

    prediction = model.predict([instruction])[0]

    print(f"Predicted Intent : {prediction}")