# 30 Day A/Bs

An A/B test simulator that generates realistic business scenarios for experimentation and then walks through design calculations and result interpretation with a user in quiz format.

## The Story Behind 30 Day A/Bs

This project was born out of a need to practice experimental design and statistical analysis in a realistic, interview-style environment. 

**The Problem**: Traditional A/B testing education is typically:
- Textbook commentary and high-level concept overviews
- Theoretical knowledge without hands-on practice
- No experience with real experimental data and statistical interpretation
- Missing the practical skills needed for actual scenarios

**The Solution**: 30 Day A/Bs provides a comprehensive simulator that generates realistic business scenarios using AI, then challenges you to design experiments and analyze results just like you would in a real interview, even simulating experimental datasets for evaluation.

**Why "30 Day A/Bs"?** While practicing experimentation won't get you abs, it might get you a solid understanding of A/Bs! Let's build some statistical fitness. 🏋️‍♂️📊

## Try It Now

### 🚀 Streamlit Cloud (Recommended)

The easiest way to use 30 Day A/Bs is through Streamlit Cloud:

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-name.streamlit.app)

Simply click the badge above to start practicing A/B testing scenarios immediately!

### 📱 What You'll Experience

1. **Generate Scenarios**: AI creates realistic business contexts with proper statistical parameters
2. **Design Experiments**: Practice sample size calculations and experimental design
3. **Analyze Data**: Download simulated data and perform statistical analysis
4. **Get Feedback**: Receive automated scoring and improvement suggestions

## Key Features

- **🤖 AI-Generated Scenarios**: Realistic business contexts with proper statistical parameters
- **📊 Deterministic Math Engine**: Consistent, reproducible calculations
- **📈 Interactive Analysis**: Statistical tests with visualizations
- **📋 Automated Scoring**: Multi-criteria evaluation with detailed feedback
- **💾 Data Export**: Download simulated datasets as CSV
- **📚 Analysis Templates**: Jupyter notebooks for advanced analysis

## Local Development

If you want to run this locally or contribute to the project:

```bash
# Clone the repository
git clone https://github.com/chrisrogers37/30-day-abs.git
cd 30-day-abs

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run ui/streamlit_app.py
```

**Required**: Add an OpenAI API key for scenario generation:
```bash
echo "OPENAI_API_KEY=your_key_here" > .env
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LLM Layer     │    │   Core Engine   │    │   UI Layer      │
│                 │    │                 │    │                 │
│ • Scenario Gen  │───▶│ • Math Engine   │◀───│ • Streamlit     │
│ • JSON Parsing  │    │ • Simulation    │    │ • Data Viz      │
│ • Guardrails    │    │ • Analysis      │    │ • User Interface│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

Built with Streamlit, Python, and modern statistical tools. Designed for experimentation and statistics education.

## Contact

**Christopher Rogers**  
[LinkedIn](https://linkedin.com/in/chrisrogers37) • [Website](https://crog.gg) • [Email](mailto:christophertrogers37@gmail.com)