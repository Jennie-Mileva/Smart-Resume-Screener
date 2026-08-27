const API_BASE_URL = "https://smart-resume-screener-api-xisb.onrender.com";

const form = document.getElementById("screenForm");
const jobTitleInput = document.getElementById("jobTitle");
const jobDescriptionInput = document.getElementById("jobDescription");
const resumeFilesInput = document.getElementById("resumeFiles");
const fileInfo = document.getElementById("fileInfo");
const screenButton = document.getElementById("screenButton");
const status = document.getElementById("status");
const resultsSection = document.getElementById("resultsSection");
const resultsSummary = document.getElementById("resultsSummary");
const resultsContainer = document.getElementById("results");

resumeFilesInput.addEventListener("change", () => {
    const files = resumeFilesInput.files;

    if (!files.length) {
        fileInfo.textContent = "No files selected";
        return;
    }

    fileInfo.textContent = `${files.length} resume(s) selected`;
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const files = resumeFilesInput.files;

    if (!files.length) {
        showStatus("Please select at least one resume.", "error");
        return;
    }

    screenButton.disabled = true;
    screenButton.textContent = "SCREENING...";
    showStatus("Screening candidates...", "loading");

    const jobDescription = buildJobDescription();

    const formData = new FormData();

    for (const file of files) {
        formData.append("resume_files", file);
    }

    const jdBlob = new Blob(
        [jobDescription],
        { type: "text/plain" }
    );

    formData.append(
        "job_description_file",
        jdBlob,
        "job_description.txt"
    );

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/resume/screen`,
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Screening failed."
            );
        }

        displayResults(data);

        showStatus(
            "Screening completed successfully.",
            "success"
        );

    } catch (error) {
        console.error(error);

        showStatus(
            error.message || "Unable to connect to the API.",
            "error"
        );

        resultsSection.classList.add("hidden");

    } finally {
        screenButton.disabled = false;
        screenButton.textContent = "SCREEN CANDIDATES";
    }
});

function buildJobDescription() {
    const title = jobTitleInput.value.trim();
    const description = jobDescriptionInput.value.trim();

    return `${title}\n\n${description}`;
}

function displayResults(data) {
    resultsContainer.innerHTML = "";

    resultsSummary.textContent =
        `${data.candidate_count} candidate(s) screened for ${data.job_title}.`;

    data.candidates.forEach((candidate) => {
        const card = document.createElement("div");

        card.className = "result-card";

        const classificationClass =
            getClassificationClass(candidate.classification);

        card.innerHTML = `
            <div class="result-top">
                <div>
                    <div class="candidate-name">
                        ${escapeHtml(candidate.candidate_name)}
                    </div>

                    <div class="filename">
                        ${escapeHtml(candidate.resume_filename)}
                    </div>
                </div>

                <div class="score">
                    ${Number(candidate.score).toFixed(1)}/10
                </div>
            </div>

            <span class="classification ${classificationClass}">
                ${escapeHtml(candidate.classification)}
            </span>

            ${renderSkills(
                "Matched Skills",
                candidate.matched_skills,
                "skill"
            )}

            ${renderSkills(
                "Missing Skills",
                candidate.missing_skills,
                "skill missing"
            )}

            <div class="justification">
                <strong>Justification</strong>
                <p>
                    ${escapeHtml(
                        candidate.justification || "No justification provided."
                    )}
                </p>
            </div>
        `;

        resultsContainer.appendChild(card);
    });

    resultsSection.classList.remove("hidden");
}

function renderSkills(title, skills, className) {
    if (!skills || !skills.length) {
        return "";
    }

    const skillItems = skills
        .map(
            (skill) =>
                `<span class="${className}">
                    ${escapeHtml(skill)}
                </span>`
        )
        .join("");

    return `
        <div class="skills">
            <strong>${title}</strong>
            <div class="skill-list">
                ${skillItems}
            </div>
        </div>
    `;
}

function getClassificationClass(classification) {
    if (classification === "Strong Match") {
        return "strong";
    }

    if (classification === "Consider") {
        return "consider";
    }

    return "not-recommended";
}

function showStatus(message, type) {
    status.textContent = message;
    status.className = `status ${type}`;
}

function escapeHtml(value) {
    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}