
document.addEventListener("DOMContentLoaded", function () {

    const dataElement = document.getElementById("diagnostic-data");

    if (!dataElement) {
        console.error("Diagnostic data not found.");
        return;
    }

    let questions;

    try {
        questions = JSON.parse(dataElement.textContent);
    } catch (error) {
        console.error("Invalid diagnostic question data:", error);
        return;
    }

    if (!Array.isArray(questions) || questions.length === 0) {
        console.error("No questions available.");
        return;
    }

    const quizSection = document.getElementById("quiz-section");
    const resultSection = document.getElementById("result-section");

    const questionText = document.getElementById("question-text");
    const questionCounter = document.getElementById("question-counter");
    const progressText = document.getElementById("progress-text");
    const progressBar = document.getElementById("progress-bar");

    const difficultyLabel = document.getElementById("difficulty-label");
    const conceptLabel = document.getElementById("concept-label");
    const optionsContainer = document.getElementById("options-container");

    const selectionMessage = document.getElementById("selection-message");
    const nextButton = document.getElementById("next-button");
    const errorMessage = document.getElementById("error-message");

    let currentIndex = 0;
    let selectedAnswer = null;
    let submissionStarted = false;

    const answers = [];

    function displayQuestion() {

        const question = questions[currentIndex];

        selectedAnswer = null;

        questionCounter.textContent =
            `Question ${currentIndex + 1}`;

        progressText.textContent =
            `${Math.round((currentIndex / questions.length) * 100)}% Completed`;

        progressBar.style.width =
            `${(currentIndex / questions.length) * 100}%`;

        questionText.textContent = question.question;
        difficultyLabel.textContent = question.difficulty;
        conceptLabel.textContent =
            `Physics Concept ${question.concept_id}`;

        selectionMessage.textContent =
            "Select an answer to continue.";

        optionsContainer.replaceChildren();

        question.options.forEach(function (option) {

            const button = document.createElement("button");

            button.type = "button";
            button.className = "diagnostic-option";
            button.textContent = option;

            button.addEventListener("click", function () {

                if (submissionStarted) return;

                selectedAnswer = option;

                optionsContainer
                    .querySelectorAll(".diagnostic-option")
                    .forEach(function (item) {
                        item.classList.remove("selected");
                    });

                button.classList.add("selected");

                selectionMessage.textContent = "Answer selected!";
                nextButton.disabled = false;

            });

            optionsContainer.appendChild(button);

        });

        nextButton.disabled = true;

        nextButton.textContent =
            currentIndex === questions.length - 1
                ? "Submit Diagnostic Test"
                : "Next Question →";

    }

    async function submitDiagnostic() {

        submissionStarted = true;

        nextButton.disabled = true;
        nextButton.textContent = "Submitting...";

        try {

            const response = await fetch("/api/diagnostic/submit", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    answers: answers
                })
            });

            const data = await response.json();

            if (!response.ok || data.status !== "success") {
                throw new Error(
                    data.message || "Diagnostic submission failed."
                );
            }

            const result = data.result;

            quizSection.hidden = true;
            resultSection.hidden = false;

            document.getElementById("final-percentage").textContent =
                `${Number(result.percentage).toFixed(1)}%`;

            document.getElementById("final-score").textContent =
                `${result.score} / ${result.total_questions} Correct`;

            document.getElementById("performance-message").textContent =
                result.performance;

            const breakdown =
                document.getElementById("concept-results-container");

            breakdown.replaceChildren();

            (result.concepts || []).forEach(function (item) {

                const card = document.createElement("div");
                card.className = "concept-result-item";

                const heading = document.createElement("h3");
                heading.textContent =
                    item.concept_name || "Physics Concept";

                const score = document.createElement("p");
                score.textContent =
                    `${item.correct} / ${item.total} correct`;

                const percentage = document.createElement("p");
                percentage.textContent =
                    `${Number(item.percentage).toFixed(1)}%`;

                const level = document.createElement("p");
                level.textContent =
                    `Mastery: ${item.level}`;

                card.append(heading, score, percentage, level);
                breakdown.appendChild(card);

            });

            progressText.textContent = "100% Completed";
            progressBar.style.width = "100%";

        } catch (error) {

            console.error("Diagnostic submission error:", error);

            errorMessage.textContent = error.message;
            errorMessage.hidden = false;

            submissionStarted = false;
            nextButton.disabled = false;
            nextButton.textContent = "Retry Submission";

        }

    }

    nextButton.addEventListener("click", function () {

        if (submissionStarted) return;

        errorMessage.hidden = true;

        // Retry without adding the final answer again.
        if (answers.length === questions.length) {
            submitDiagnostic();
            return;
        }

        if (selectedAnswer === null) {
            errorMessage.textContent = "Please select an answer.";
            errorMessage.hidden = false;
            return;
        }

        answers.push({
            question_id: questions[currentIndex].id,
            selected_answer: selectedAnswer
        });

        if (currentIndex < questions.length - 1) {

            currentIndex++;
            displayQuestion();

        } else {

            submitDiagnostic();

        }

    });

    displayQuestion();

});
