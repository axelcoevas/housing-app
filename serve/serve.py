from flask import Flask, request, jsonify
import joblib
import numpy as np

app = Flask(__name__)

model = joblib.load('/data/california_housing_model.pkl')
scaler = joblib.load('/data/scaler.pkl')

FEATURE_ORDER = ['MedInc', 'HouseAge', 'AveRooms', 'AveBedrms',
                  'Population', 'AveOccup', 'Latitude', 'Longitude']

@app.route('/predict', methods=['POST'])
def predict():
    payload = request.get_json()

    try:
        features = [payload[f] for f in FEATURE_ORDER]
    except KeyError as e:
        return jsonify({'error': f'Falta el campo {e}'}), 400

    features_scaled = scaler.transform(np.array(features).reshape(1, -1))
    prediction = model.predict(features_scaled)[0]

    return jsonify({'predicted_price_hundreds_of_thousands': round(float(prediction), 4)})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)