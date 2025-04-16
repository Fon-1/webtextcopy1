# Universal Content Extractor

A powerful web content extraction tool built with Streamlit that can extract readable content from any webpage, with special support for novel and article websites.

## Features

- 🌐 Universal content extraction from any webpage
- 📚 Special support for novel and article websites
- 🎨 Customizable reading experience (font size, theme, line height)
- 📝 Annotation and bookmarking system
- 📱 Responsive design
- 🔄 Chapter navigation support
- 💾 Save content as text files
- 📋 Copy to clipboard functionality

## Mobile Access Setup (Streamlit Cloud)

1. Create a GitHub account if you don't have one
2. Create a new repository on GitHub
3. Push your code to GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```
4. Go to [Streamlit Cloud](https://streamlit.io/cloud)
5. Sign in with your GitHub account
6. Click "New app"
7. Select your repository, branch (main), and file (a.py)
8. Click "Deploy"

Your app will be available at: `https://<your-app-name>.streamlit.app`

## Local Installation

### Using pip

```bash
# Clone the repository
git clone <your-repo-url>
cd text_summary

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run a.py
```

### Using Conda

```bash
# Clone the repository
git clone <your-repo-url>
cd text_summary

# Create and activate conda environment
conda env create -f environment.yml
conda activate content_extractor

# Run the application
streamlit run a.py
```

### Using Docker

```bash
# Build the Docker image
docker build -t content-extractor .

# Run the container
docker run -p 8501:8501 content-extractor
```

## Usage

1. Open the app URL in your mobile browser
2. Enter a URL in the input field
3. Click "Trích xuất" to extract the content
4. Use the sidebar (menu icon on mobile) for customization options:
   - Adjust font size
   - Change theme (light/dark)
   - Modify line height
   - Change font family
5. Use the annotation feature to add notes
6. Navigate between chapters using the buttons
7. Download or copy content as needed

## Mobile-Specific Features

- 📱 Responsive design optimized for mobile screens
- 👆 Touch-friendly interface
- 📖 Reading progress saves automatically
- 🔍 Easy text selection for annotations
- 🌙 Dark mode for comfortable reading

## Configuration

The application stores user preferences in a `preferences.json` file, which includes:

- Reading preferences (font size, theme, etc.)
- Reading history
- Annotations

## Development

To contribute to the project:

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Submit a pull request

## Troubleshooting

### Mobile Browser Issues
- Enable JavaScript in your mobile browser
- Allow cookies for saving preferences
- Clear browser cache if experiencing issues

### SSL Issues
Some websites may have SSL certificate issues. The application will automatically handle these cases by disabling SSL verification when necessary.

### Timeout Issues
For slow websites, you can adjust the timeout settings in the code. Default timeout is 30 seconds.

### Content Extraction Issues
If content extraction fails:
- Check if the website allows scraping
- Try using a different browser User-Agent
- Check if the website requires authentication

## License

This project is licensed under the MIT License - see the LICENSE file for details. # webtextcopy
