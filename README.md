# Rhombus AI – Test Automation Suite

## Project Structure
rhombus-ai-tests/
├── ui-tests/                        # Part 1 – UI Automation (Playwright)
│   ├── conftest.py
│   ├── pytest.ini
│   ├── .env
│   ├── fixtures/
│   │   └── messy_data.csv
│   └── tests/
│       └── test_ai_pipeline_flow.py
├── api-tests/                       # Part 2 – API Tests
│   ├── conftest.py
│   ├── pytest.ini
│   ├── .env
│   ├── fixtures/
│   │   └── messy_data.csv
│   └── test_api.py
├── data-validation/                 # Part 3 – Data Validation
│   └── validate.py
└── README.md

---

## Setup

### Prerequisites
- Python 3.11+
- pip

### Install dependencies

```bash
# From the project root
pip install pytest pytest-playwright pytest-html requests python-dotenv pandas
playwright install chromium
```

### Configure credentials
Both `ui-tests/.env` and `api-tests/.env` must contain:
RHOMBUS_EMAIL=your@email.com
RHOMBUS_PASSWORD=yourpassword
RHOMBUS_BASE_URL=https://rhombusai.com

---

## Part 1 – UI Automation

Tests the full AI Pipeline Flow using Playwright:
1. Sign in
2. Upload a messy CSV file
3. Prompt the AI to clean the data
4. Wait for pipeline execution
5. Preview the output
6. Download the results

### Run

```bash
cd ui-tests

# Headless
pytest tests/ -v

# Headed (watch the browser)
pytest tests/ -v --headed

# With HTML report
pytest tests/ -v --headed --html=report.html
```

---

## Part 2 – API Tests

Black-box API tests covering:
- Authentication and session behaviour
- Dataset upload
- Pipeline execution status
- Download endpoints
- Error handling for invalid input

### Run

```bash
cd api-tests
pytest -v

# With HTML report
pytest -v --html=report.html
```

---

## Part 3 – Data Validation

Validates that the AI pipeline correctly transformed the input CSV by checking:
- Output schema correctness
- Row counts
- No empty IDs
- Dates formatted as YYYY-MM-DD
- Salary is numeric with no currency symbols
- Names are in Title Case
- Phone numbers are formatted correctly

### Run

```bash
cd data-validation

python validate.py \
  --input ../ui-tests/fixtures/messy_data.csv \
  --output path/to/downloaded_output.csv
```

Replace `path/to/downloaded_output.csv` with the actual path to the file
you downloaded from Rhombus AI after running the pipeline.

---

## Demo Video

[Link to demo video]

---

## Notes

- The test suite uses a black-box approach throughout — no assumptions about
  internal implementation details.
- API tests use endpoint probing to stay valid even if exact paths change.
- UI tests use session state caching to avoid repeated logins.
- Data validation checks correctness of transformation, not just workflow completion.


