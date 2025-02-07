from flask import Flask, render_template, request, jsonify
import requests
import os
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)

# API Key and Endpoint for Plant.id
API_KEY = "FRSaEd1HFSWGj7pWbTBuvlM1AK5HC4GPxy7fC1NEpmwdSQXGtv"
API_URL = "https://api.plant.id/v2/identify"  # Corrected API endpoint

# Set upload folder for images
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# List of non-weed plants (e.g., crops like paddy)
NON_WEED_PLANTS = ['Oryza sativa', 'Triticum aestivum', 'Zea mays', 'Solanum tuberosum', 
                   'Capsicum annuum', 'Cucumis sativus', 'Lycopersicon esculentum', 'Allium cepa', 
                   'Brassica oleracea', 'Cucurbita pepo', 'Carthamus tinctorius', 'Vigna unguiculata', 
                   'Cicer arietinum', 'Phaseolus vulgaris', 'Medicago sativa', 'Helianthus annuus',
                   'Fagopyrum esculentum', 'Glycine max', 'Hordeum vulgare', 'Arachis hypogaea', 
                   'Cucurbita maxima', 'Spinacia oleracea', 'Beta vulgaris', 'Daucus carota',
                   'Brassica napus', 'Asparagus officinalis', 'Coriandrum sativum', 'Petroselinum crispum', 
                   'Lactuca sativa', 'Raphanus sativus', 'Allium sativum', 'Zingiber officinale', 
                   'Solanum lycopersicum', 'Cucumis melo', 'Capsicum frutescens', 'Ricinus communis', 
                   'Apteryx australis', 'Vitis vinifera', 'Carya illinoinensis', 'Prunus persica', 
                   'Prunus avium', 'Prunus domestica', 'Malus domestica', 'Citrus sinensis', 
                   'Citrus limon', 'Citrus paradisi', 'Fragaria × ananassa', 'Vaccinium corymbosum', 
                   'Ficus carica', 'Pyrus calleryana', 'Persea americana', 'Mangifera indica', 
                   'Carica papaya', 'Carya ovata', 'Tamarindus indica', 'Cinnamomum verum', 
                   'Ficus elastica', 'Syzygium jambos', 'Chamaedorea elegans', 'Camellia sinensis',
                   'Phoenix dactylifera', 'Rosa rugosa', 'Geranium maculatum', 'Aloe vera', 
                   'Ginkgo biloba', 'Prunus cerasus', 'Linum usitatissimum', 'Acer saccharum', 
                   'Liquidambar styraciflua', 'Ailanthus altissima', 'Liriodendron tulipifera', 
                   'Betula pendula', 'Quercus alba', 'Pinus sylvestris', 'Picea abies', 
                   'Juniperus communis', 'Cedrus libani', 'Carya laciniosa', 'Prunus serotina', 
                   'Gleditsia triacanthos', 'Betula nigra', 'Buxus sempervirens', 'Ilex aquifolium', 
                   'Juniperus virginiana', 'Acer rubrum', 'Syringa vulgaris', 'Carya texana', 
                   'Pinus ponderosa', 'Chamaecyparis obtusa', 'Larix decidua', 'Picea pungens', 
                   'Taxodium distichum']
  # Add any known crops that are not weeds

def allowed_file(filename):
    """Check if the uploaded file is an allowed image."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Homepage for uploading images."""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Handle image upload and weed identification."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'})
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'})

    if file and allowed_file(file.filename):
        # Save the file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Call the Plant.id API for identification
        with open(filepath, 'rb') as img_file:
            response = requests.post(
                API_URL,
                headers={'Api-Key': API_KEY},
                files={'images': img_file},
                data={'organs': 'leaf'}  # Specify the organ type (leaf, flower, etc.)
            )
        
        # Process the API response
        if response.status_code == 200:
            result = response.json()
            if 'suggestions' in result and len(result['suggestions']) > 0:
                top_suggestion = result['suggestions'][0]
                weed_name = top_suggestion['plant_name']
                confidence = top_suggestion['probability'] * 100  # Convert to percentage

                # Check if the weed is a known non-weed plant
                if weed_name in NON_WEED_PLANTS:
                    return jsonify({
                        'WeedType': weed_name,
                        'Confidence': f"{confidence:.2f}%",
                        'isWeed': False,
                        'Message': "This is not a weed.",
                        'ControlMeasure': "Manual weeding, use of herbicides, crop rotation.",
                        'Climate': "Tropical and subtropical regions.",
                        'AdditionalInfo': "Commonly known as rice, a major staple food crop.",
                        'ImagePath': filepath
                    })
                elif confidence < 70:  # If the confidence is low, consider it as "Not Identified"
                    return jsonify({
                        'WeedType': "Not Identified",
                        'Confidence': f"{confidence:.2f}%",
                        'isWeed': False,
                        'Message': "The plant could not be confidently identified as a weed.",
                        'ControlMeasure': "",
                        'Climate': "",
                        'AdditionalInfo': "",
                        'ImagePath': filepath
                    })
                else:
                    return jsonify({
                        'WeedType': weed_name,
                        'Confidence': f"{confidence:.2f}%",
                        'isWeed': True,
                        'Message': "This is a weed.",
                        'ControlMeasure': "Herbicides, manual removal, crop rotation.",
                        'Climate': "Warm, temperate regions",
                        'AdditionalInfo': "Invasive plant that affects crops and health.",
                        'ImagePath': filepath
                    })
            else:
                return jsonify({'error': 'No weed detected in the image'})
        else:
            return jsonify({'error': 'API request failed', 'details': response.text})
    else:
        return jsonify({'error': 'Invalid file format'})

if __name__ == '__main__':
    # Ensure upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)