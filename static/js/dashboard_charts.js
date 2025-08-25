document.addEventListener('DOMContentLoaded', () => {
    // Asegurar que chartData esté definido
    if (!window.chartData) {
        console.error('window.chartData no está definido');
        window.chartData = {};
    }

    // Lógica de filtrado de botones
    let activeFilter = null;
    document.querySelectorAll('.filter-btn').forEach(button => {
        button.addEventListener('click', () => {
            const status = button.getAttribute('data-status');
            const items = document.querySelectorAll('.problem-item');

            if (activeFilter === status) {
                // Desactivar filtro
                activeFilter = null;
                button.classList.remove('active');
                items.forEach(item => item.style.display = 'block');
            } else {
                // Activar filtro
                activeFilter = status;
                document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                items.forEach(item => {
                    if (item.getAttribute('data-status') === status) {
                        item.style.display = 'block';
                    } else {
                        item.style.display = 'none';
                    }
                });
            }
        });
    });

    // Gráfico de puntuación WooRank (Gauge)
    const scoreCanvas = document.getElementById('woorankScoreChart');
    if (scoreCanvas && window.chartData.woorank && window.chartData.woorank.score !== undefined) {
        try {
            const score = Number(window.chartData.woorank.score) || 0;
            if (score >= 0 && score <= 100) {
                const scoreCtx = scoreCanvas.getContext('2d');
                new Chart(scoreCtx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Puntuación', 'Restante'],
                        datasets: [{
                            data: [score, 100 - score],
                            backgroundColor: [
                                score >= 70 ? 'rgba(40, 167, 69, 0.5)' : score >= 40 ? 'rgba(255, 193, 7, 0.5)' : 'rgba(220, 53, 69, 0.5)',
                                'rgba(200, 200, 200, 0.2)'
                            ],
                            borderColor: [
                                score >= 70 ? 'rgba(40, 167, 69, 1)' : score >= 40 ? 'rgba(255, 193, 7, 1)' : 'rgba(220, 53, 69, 1)',
                                'rgba(200, 200, 200, 1)'
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        circumference: 180,
                        rotation: -90,
                        cutout: '70%',
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return `${context.label}: ${context.raw}%`;
                                    }
                                }
                            }
                        },
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
            } else {
                console.error('Puntuación de WooRank no válida:', score);
            }
        } catch (error) {
            console.error('Error al generar el gráfico de puntuación de WooRank:', error);
        }
    } else if (scoreCanvas) {
        console.warn('No hay datos de puntuación de WooRank válidos para el gráfico.');
    }

    // Gráfico de problemas por estado
    const issuesCanvas = document.getElementById('woorankIssuesChart');
    if (issuesCanvas && window.chartData.woorank && window.chartData.woorank.problemas) {
        try {
            const problemas = window.chartData.woorank.problemas;
            const statusCounts = {
                good: 0,
                neutral: 0,
                bad: 0
            };

            // Contar problemas por estado
            Object.values(problemas).forEach(problema => {
                const status = problema.status ? problema.status.toLowerCase() : 'neutral';
                if (['good', 'neutral', 'bad'].includes(status)) {
                    statusCounts[status]++;
                } else {
                    statusCounts['neutral']++; // Por defecto, usar neutral
                }
            });

            const statusLabels = ['Good', 'Neutral', 'Bad'];
            const statusValues = [statusCounts.good, statusCounts.neutral, statusCounts.bad];

            if (statusLabels.length > 0) {
                const issuesCtx = issuesCanvas.getContext('2d');
                new Chart(issuesCtx, {
                    type: 'bar',
                    data: {
                        labels: statusLabels,
                        datasets: [{
                            label: 'Número de Problemas',
                            data: statusValues,
                            backgroundColor: [
                                'rgba(40, 167, 69, 0.5)',  // Good: Verde
                                'rgba(255, 193, 7, 0.5)',  // Neutral: Amarillo
                                'rgba(220, 53, 69, 0.5)'   // Bad: Rojo
                            ],
                            borderColor: [
                                'rgba(40, 167, 69, 1)',
                                'rgba(255, 193, 7, 1)',
                                'rgba(220, 53, 69, 1)'
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: { beginAtZero: true, ticks: { stepSize: 1 } }
                        },
                        plugins: {
                            legend: { display: true },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return `${context.label}: ${context.raw} problema(s)`;
                                    }
                                }
                            }
                        }
                    }
                });
            } else {
                console.warn('No hay problemas con estados válidos para el gráfico.');
            }
        } catch (error) {
            console.error('Error al generar el gráfico de problemas de WooRank:', error);
        }
    } else if (issuesCanvas) {
        console.warn('No hay datos de problemas de WooRank válidos para el gráfico.');
    }

    window.showMore = function(btn) {
        btn.nextElementSibling.style.display = 'block';
        btn.style.display = 'none';
    };
});