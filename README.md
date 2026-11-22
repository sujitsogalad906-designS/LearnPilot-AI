\# LearnPilot-AI

\### Adaptive Exam-Prep Tutor with a Learner Model



LearnPilot-AI is an intelligent, adaptive exam-preparation platform designed to help students improve their learning through personalized assessments, practice quizzes, performance tracking, and revision support.



The platform aims to move beyond one-size-fits-all exam preparation by identifying individual learning gaps and providing a more structured learning experience.



\## Key Features



\- \*\*Student Authentication:\*\* Student registration and login.

\- \*\*Personalized Dashboard:\*\* Overview of learning progress and performance.

\- \*\*Physics Concept Library:\*\* Organized learning resources for Physics concepts.

\- \*\*Diagnostic Assessment:\*\* Evaluates students' initial knowledge and understanding.

\- \*\*Practice Quizzes:\*\* Interactive quizzes with answer evaluation.

\- \*\*Learner Model:\*\* Tracks concept-wise performance and mastery.

\- \*\*Performance Analytics:\*\* Helps students understand their strengths and areas for improvement.

\- \*\*Revision Support:\*\* Supports focused revision based on learning progress.

\- \*\*AI Integration:\*\* Uses an AI service for supported intelligent learning features.



\## Technology Stack



| Component | Technology |

|---|---|

| Backend | Python, Flask |

| Frontend | HTML, CSS, JavaScript |

| Database | SQLite, Flask-SQLAlchemy |

| AI Integration | OpenAI API |

| Data Storage | JSON |

| Testing | Pytest |



\## Project Structure



```text

LearnPilot-AI/

│

├── agents/

├── data/

├── database/

├── services/

├── static/

│   ├── css/

│   └── js/

├── templates/

├── tests/

│

├── app.py

├── config.py

├── requirements.txt

├── .env.example

├── .gitignore

└── README.md

```



\## Installation and Setup



\### 1. Clone the Repository



```bash

git clone https://github.com/sujitsogalad906-designS/LearnPilot-AI.gitcd LearnPilot-AI

```



\### 2. Create a Virtual Environment



```bash

python -m venv .venv

```



\### 3. Activate the Environment



\*\*Windows Command Prompt:\*\*



```cmd

.venv\\Scripts\\activate

```



\### 4. Install Dependencies



```bash

pip install -r requirements.txt

```



\### 5. Configure Environment Variables



Create a `.env` file using the example configuration:



```cmd

copy .env.example .env

```



Open `.env` and configure your own values:



```text

SECRET\_KEY=your-random-secret-key

OPENAI\_API\_KEY=your-openai-api-key

DATABASE\_URL=sqlite:///learnpilot.db

```



Keep your actual `.env` file private. Never publish API keys or secret credentials.



\### 6. Run the Application



```bash

python app.py

```



Open your browser and visit:



```text

http://127.0.0.1:5000

```



The application initializes its database tables when the Flask application is created.



\## Running Tests



Run the test suite using:



```bash

pytest

```



\## Project Objective



To develop an adaptive exam-preparation tutor that supports students through diagnostic assessments, learner performance tracking, personalized practice, and revision assistance.



\## Future Enhancements



\- More advanced adaptive learning recommendations.

\- Expanded subject and question-bank support.

\- Enhanced learning analytics.

\- Improved personalized revision scheduling.



\## Acknowledgement



Developed as part of the \*\*Product Space Agentic AI Hackathon 2026\*\*.



\---



\*\*LearnPilot-AI – Learn Smarter. Practice Better. Improve Continuously.\*\*



