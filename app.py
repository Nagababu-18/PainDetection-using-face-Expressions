from flask import Flask, request, jsonify, render_template
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import io

app = Flask(__name__)

# Device config
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load model
model = models.resnet18(pretrained=False)
model.fc = nn.Linear(model.fc.in_features, 7)  # 7 output classes
model.load_state_dict(torch.load('emotion_model.pth', map_location=device))
model.to(device)
model.eval()

# Class labels
emotion_labels = ['happy', 'neutral', 'surprise', 'sad', 'angry', 'fear', 'disgust']

# Emotion → Pain mapping
def map_emotion_to_pain(emotion):
    mapping = {
        'happy': ("No Pain", "You're doing great. Keep it up!"),
        'neutral': ("No/Mild Pain", "Monitor if changes occur."),
        'surprise': ("Mild Pain", "Take a rest. Observe the symptoms."),
        'sad': ("Moderate Pain", "Try relaxation, hydration, or support."),
        'angry': ("Moderate/High Pain", "Could indicate discomfort—stay calm."),
        'fear': ("High Pain", "Breathe deeply, reduce stimuli."),
        'disgust': ("Severe Pain", "Immediate attention may be needed.")
    }
    return mapping.get(emotion.lower(), ("Unknown", "No suggestion available."))

# Image Transform
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    image = Image.open(io.BytesIO(file.read())).convert('RGB')
    image = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(image)
        _, predicted = torch.max(output, 1)
        emotion = emotion_labels[predicted.item()]
        pain_level, suggestion = map_emotion_to_pain(emotion)

    return jsonify({
        'emotion': emotion,
        'pain_level': pain_level,
        'suggestion': suggestion
    })

if __name__ == '__main__':
    app.run(debug=True)
