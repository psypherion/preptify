// Initialize the charts when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Use the dynamically injected csvFilePath variable from charts.html
        if (!csvFilePath) {
            console.error("CSV file path is not defined.");
            return;
        }

        // Fetch and parse the CSV file
        const response = await fetch(csvFilePath);
        if (!response.ok) {
            throw new Error(`Failed to fetch CSV file from ${csvFilePath}`);
        }

        const csvData = await response.text();
        const parsedData = Papa.parse(csvData, { header: true, skipEmptyLines: true });

        // Process the parsed CSV data
        if (parsedData.data.length === 0) {
            console.error("CSV file is empty or has invalid content.");
            return;
        }

        initializeCharts(parsedData.data);
        populateTopicsList(parsedData.data);
        setupTopicSelection(parsedData.data);
    } catch (error) {
        console.error("Error initializing charts:", error);
    }
});

// Function to initialize charts with data
function initializeCharts(data) {
    google.charts.load('current', { packages: ['corechart'] });
    google.charts.setOnLoadCallback(() => {
        drawTopTopicsChart(data);
        drawAnswerFrequencyChart(data);
        drawImportantUnitsChart(data);
    });

    // Add event listener for the "Update Charts" button
    const updateChartsBtn = document.getElementById('updateChartsBtn');
    if (updateChartsBtn) {
        updateChartsBtn.addEventListener('click', () => {
            const topNTopics = parseInt(document.getElementById('topNTopics').value, 10) || 5;
            drawTopTopicsChart(data, topNTopics);
        });
    }
}

// Function to populate the topics list in the sidebar
function populateTopicsList(data) {
    const topicsList = document.getElementById('topicsList');
    if (!topicsList) return;

    const uniqueTopics = [...new Set(data.map(row => row.Topic))];
    uniqueTopics.forEach(topic => {
        const topicLink = document.createElement('a');
        topicLink.textContent = topic;
        topicLink.href = `#${topic}`;
        topicsList.appendChild(topicLink);
    });
}

// Function to set up topic selection dropdown and display questions
function setupTopicSelection(data) {
    const topicSelect = document.getElementById('importantTopicsSelect');
    const topicQuestionsContainer = document.getElementById('topic-questions-container');

    if (!topicSelect || !topicQuestionsContainer) return;

    const uniqueTopics = [...new Set(data.map(row => row.Topic))];
    uniqueTopics.forEach(topic => {
        const option = document.createElement('option');
        option.value = topic;
        option.textContent = topic;
        topicSelect.appendChild(option);
    });

    topicSelect.addEventListener('change', () => {
        const selectedTopic = topicSelect.value;
        topicQuestionsContainer.innerHTML = '';

        if (selectedTopic) {
            const questions = data.filter(row => row.Topic === selectedTopic);
            if (questions.length > 0) {
                const table = document.createElement('table');
                const headerRow = document.createElement('tr');
                ['Question', 'Answer'].forEach(headerText => {
                    const th = document.createElement('th');
                    th.textContent = headerText;
                    headerRow.appendChild(th);
                });
                table.appendChild(headerRow);

                questions.forEach(row => {
                    const dataRow = document.createElement('tr');
                    const questionCell = document.createElement('td');
                    const answerCell = document.createElement('td');
                    questionCell.textContent = row.Question;
                    answerCell.textContent = row.Answer;
                    dataRow.appendChild(questionCell);
                    dataRow.appendChild(answerCell);
                    table.appendChild(dataRow);
                });

                topicQuestionsContainer.appendChild(table);
            } else {
                topicQuestionsContainer.textContent = "No questions found for this topic.";
            }
        }
    });
}

// Function to draw the Top Topics chart
function drawTopTopicsChart(data, topN = 5) {
    const topicCounts = {};
    data.forEach(row => {
        if (row.Topic) {
            topicCounts[row.Topic] = (topicCounts[row.Topic] || 0) + 1;
        }
    });

    const sortedTopics = Object.entries(topicCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, topN);

    const chartData = new google.visualization.DataTable();
    chartData.addColumn('string', 'Topic');
    chartData.addColumn('number', 'Frequency');
    chartData.addRows(sortedTopics);

    const chart = new google.visualization.PieChart(document.getElementById('topTopicsChart'));
    chart.draw(chartData, { title: 'Top Topics', is3D: true });
}

// Function to draw the Answer Frequency chart
function drawAnswerFrequencyChart(data) {
    const answerCounts = { 'Correct': 0, 'Incorrect': 0 };
    data.forEach(row => {
        if (row.Correct === 'Yes') {
            answerCounts['Correct']++;
        } else if (row.Correct === 'No') {
            answerCounts['Incorrect']++;
        }
    });

    const chartData = new google.visualization.DataTable();
    chartData.addColumn('string', 'Answer Type');
    chartData.addColumn('number', 'Frequency');
    chartData.addRows(Object.entries(answerCounts));

    const chart = new google.visualization.PieChart(document.getElementById('answerFrequencyChart'));
    chart.draw(chartData, { title: 'Answer Frequency', pieHole: 0.4 });
}

// Function to draw the Important Units chart
function drawImportantUnitsChart(data) {
    const unitCounts = {};
    data.forEach(row => {
        if (row.ImportantUnit) {
            unitCounts[row.ImportantUnit] = (unitCounts[row.ImportantUnit] || 0) + 1;
        }
    });

    const chartData = new google.visualization.DataTable();
    chartData.addColumn('string', 'Unit');
    chartData.addColumn('number', 'Frequency');
    chartData.addRows(Object.entries(unitCounts));

    const chart = new google.visualization.ColumnChart(document.getElementById('importantUnitsChart'));
    chart.draw(chartData, { title: 'Important Units', hAxis: { title: 'Units' }, vAxis: { title: 'Frequency' } });
}
