
document.addEventListener("DOMContentLoaded", function () {

    const dataElement = document.getElementById("question-data");

    if (!dataElement) {
        return;
    }

    const questions = JSON.parse(dataElement.textContent);

    const questionCounter = document.getElementById("question-counter");
    const progressText = document.getElementById("progress-text");
    const progressBar = document.getElementById("progress-bar");

    const questionText = document.getElementById("question-text");
    const difficultyText = document.getElementById("question-difficulty");
    const optionsContainer = document.getElementById("options-container");

    const feedback = document.getElementById("feedback");
    const nextButton = document.getElementById("next-button");

    const quizCard = document.getElementById("quiz-card");
    const resultCard = document.getElementById("result-card");

    const finalScore = document.getElementById("final-score");
    const resultMessage = document.getElementById("result-message");
    const resultPercentage = document.getElementById("result-percentage");

    const restartButton = document.getElementById("restart-button");

    let currentQuestion = 0;
    let score = 0;
    let answered = false;
    let resultSaved = false;
    let savingResult = false;

        let userAnswers = [];

    // Display database saving status
    const saveStatus = document.createElement("p");
    saveStatus.id = "save-status";
    saveStatus.className = "save-status";
    resultPercentage.insertAdjacentElement("afterend", saveStatus);

    // Display current question
    function displayQuestion() {

        if (currentQuestion >= questions.length) {
            showResults();
            return;
        }

        const question = questions[currentQuestion];

        answered = false;

        questionCounter.textContent =
            `Question ${currentQuestion + 1} of ${questions.length}`;

        const progress = Math.round(
            (currentQuestion / questions.length) * 100
        );

        progressText.textContent = `${progress}% Completed`;
        progressBar.style.width = `${progress}%`;

        questionText.textContent = question.question;
        difficultyText.textContent = question.difficulty;

        optionsContainer.innerHTML = "";

        feedback.textContent = "";
        feedback.className = "feedback";

        nextButton.disabled = true;

        question.options.forEach(function (option) {

            const button = document.createElement("button");

            button.type = "button";
            button.className = "option-button";
            button.textContent = option;

            button.addEventListener("click", function () {
                checkAnswer(option, button);
            });

            optionsContainer.appendChild(button);

        });

        nextButton.textContent =
            currentQuestion === questions.length - 1
                ? "Finish Test →"
                : "Next Question →";
    }

    // Check selected answer
    function checkAnswer(selectedOption, selectedButton) {

        if (answered) {
            return;
        }

        answered = true;

        const question = questions[currentQuestion];

        const selectedIndex = question.options.indexOf(selectedOption);
        const selectedLetter = "ABCD"[selectedIndex];

        userAnswers.push({
            question_id: question.id,
            selected_answer: selectedLetter
        });

        const buttons = optionsContainer.querySelectorAll("button");

        buttons.forEach(function (button) {

            button.disabled = true;

            if (button.textContent === question.correct_answer) {
                button.classList.add("correct");
            }

        });

        if (selectedOption === question.correct_answer) {

            score++;

            feedback.textContent =
                "Correct answer! " + question.explanation;

            feedback.classList.add("correct");

        } else {

            selectedButton.classList.add("incorrect");

            feedback.textContent =
                "Incorrect answer. Correct answer: " +
                question.correct_answer +
                ". " +
                question.explanation;

            feedback.classList.add("incorrect");

        }

        nextButton.disabled = false;
    }

    // Show results and save them in database
    async function showResults() {

        quizCard.hidden = true;
        resultCard.hidden = false;

        const percentage = Math.round(
            (score / questions.length) * 100
        );

        finalScore.textContent =
            `${score}/${questions.length}`;

        resultPercentage.textContent =
            `Your score: ${percentage}%`;

        if (percentage >= 80) {

            resultMessage.textContent =
                "Excellent work! You have a strong understanding.";

        } else if (percentage >= 50) {

            resultMessage.textContent =
                "Good effort! Keep practising to improve.";

        } else {

            resultMessage.textContent =
                "Keep learning! Revise the concepts and try again.";

        }

        progressText.textContent = "100% Completed";
        progressBar.style.width = "100%";

        // Prevent duplicate submissions
        if (resultSaved || savingResult) {
            return;
        }

        savingResult = true;
        restartButton.disabled = true;

        saveStatus.textContent = "Saving your result...";
        saveStatus.className = "save-status";

        try {

            const response = await fetch("/api/quiz/submit", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ answers: userAnswers })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.message || "Unable to save your result."
                );
            }

            resultSaved = true;

            saveStatus.textContent =
                "✓ Your quiz result has been saved successfully!";

            saveStatus.classList.add("success");

        } catch (error) {

            console.error("Quiz saving error:", error);

            saveStatus.textContent =
                "Unable to save your result. Please try again.";

            saveStatus.classList.add("error");

        } finally {

            savingResult = false;
            restartButton.disabled = false;

        }
    }

    // Move to next question
    nextButton.addEventListener("click", function () {

        if (!answered) {
            return;
        }

        currentQuestion++;
        displayQuestion();

    });

    // Restart quiz
    restartButton.addEventListener("click", function () {

        if (savingResult) {
            return;
        }

        currentQuestion = 0;
        score = 0;
        answered = false;
        resultSaved = false;
        userAnswers = [];

        saveStatus.textContent = "";
        saveStatus.className = "save-status";

        quizCard.hidden = false;
        resultCard.hidden = true;

        displayQuestion();

    });

    // Handle empty question list
    if (questions.length === 0) {

        questionText.textContent =
            "No questions are currently available.";

        nextButton.hidden = true;
        return;

    }

    displayQuestion();

});

