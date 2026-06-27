FROM python:3.11-slim

LABEL maintainer="TRANSIT-AI"
LABEL description="Exoplanet Detection Pipeline"

# System dependencies for batman, scipy, astropy
RUN apt-get update && apt-get install -y \
    gcc g++ gfortran \
    libopenblas-dev liblapack-dev \
    git curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .
RUN pip install -e .

# Create data directories
RUN mkdir -p data/{raw,processed,synthetic,training,validation,results} \
             models reports logs

# Generate synthetic training data at build time
RUN python -c "
from src.acquisition.synthetic_generator import generate_training_dataset
df = generate_training_dataset(n_per_class=500)
print(f'Pre-generated {len(df)} training samples')
"

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app/streamlit_app.py", \
     "--server.port=8501", "--server.address=0.0.0.0", \
     "--server.headless=true", "--browser.gatherUsageStats=false"]
