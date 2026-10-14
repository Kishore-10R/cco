
from flask import Flask, render_template_string, request

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Cloud Cost Monitoring and Optimisation</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            font-family: Arial, sans-serif;
            margin: 0;
            background: #f1f5f9;
            color: #1e293b;
        }

        header {
            background: #123c69;
            color: white;
            text-align: center;
            padding: 30px 15px;
        }

        header h1 {
            margin: 0 0 10px;
        }

        .container {
            max-width: 1000px;
            margin: 30px auto;
            padding: 0 20px;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(
                auto-fit, minmax(200px, 1fr)
            );
            gap: 20px;
        }

        .card {
            background: white;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 3px 10px #00000010;
        }

        .card h3 {
            color: #64748b;
            font-size: 16px;
        }

        .amount {
            font-size: 27px;
            font-weight: bold;
            color: #087f5b;
        }

        .form-box {
            background: white;
            padding: 25px;
            margin-top: 25px;
            border-radius: 12px;
            box-shadow: 0 3px 10px #00000010;
        }

        label {
            display: block;
            margin-top: 15px;
            font-weight: bold;
        }

        input {
            width: 100%;
            padding: 12px;
            margin-top: 8px;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
        }

        button {
            width: 100%;
            padding: 13px;
            margin-top: 22px;
            background: #123c69;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
        }

        button:hover {
            background: #1d568e;
        }

        .result {
            background: #e0f2fe;
            border-left: 5px solid #0284c7;
            padding: 18px;
            margin-top: 22px;
            border-radius: 6px;
        }

        .status {
            font-weight: bold;
        }

        footer {
            text-align: center;
            padding: 25px;
            color: #64748b;
        }
    </style>
</head>

<body>
    <header>
        <h1>Cloud Cost Monitoring and Optimisation System</h1>
        <p>Monitor cloud expenses and find ways to reduce costs</p>
    </header>

    <div class="container">

        <div class="cards">
            <div class="card">
                <h3>Monthly Cloud Cost</h3>
                <div class="amount">₹{{ monthly_cost }}</div>
            </div>

            <div class="card">
                <h3>Yearly Estimated Cost</h3>
                <div class="amount">₹{{ yearly_cost }}</div>
            </div>

            <div class="card">
                <h3>Cost Status</h3>
                <div class="amount status"
                     style="font-size: 22px;">
                    {{ status }}
                </div>
            </div>
        </div>

        <div class="form-box">
            <h2>Cloud Cost Calculator</h2>

            <p>
                Enter the estimated monthly cost of your
                cloud services below.
            </p>

            <form method="POST">
                <label for="compute">Compute Cost (₹)</label>
                <input
                    type="number"
                    id="compute"
                    name="compute"
                    min="0"
                    step="0.01"
                    value="{{ compute }}"
                    required
                >

                <label for="storage">Storage Cost (₹)</label>
                <input
                    type="number"
                    id="storage"
                    name="storage"
                    min="0"
                    step="0.01"
                    value="{{ storage }}"
                    required
                >

                <label for="network">Network Cost (₹)</label>
                <input
                    type="number"
                    id="network"
                    name="network"
                    min="0"
                    step="0.01"
                    value="{{ network }}"
                    required
                >

                <button type="submit">
                    Calculate Cloud Cost
                </button>
            </form>

            {% if calculated %}
            <div class="result">
                <h3>Cost Analysis</h3>

                <p>
                    Monthly Cost:
                    <strong>₹{{ monthly_cost }}</strong>
                </p>

                <p>
                    Yearly Cost:
                    <strong>₹{{ yearly_cost }}</strong>
                </p>

                <p>
                    Status:
                    <strong>{{ status }}</strong>
                </p>

                <p>
                    <strong>Optimization Recommendation:</strong>
                    {{ recommendation }}
                </p>
            </div>
            {% endif %}
        </div>
    </div>

    <footer>
        MCA Cloud Computing Project |
        Cloud Cost Monitoring and Optimisation System
    </footer>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def home():
    compute = 0.0
    storage = 0.0
    network = 0.0
    calculated = False

    if request.method == "POST":
        compute = float(request.form.get("compute", 0))
        storage = float(request.form.get("storage", 0))
        network = float(request.form.get("network", 0))
        calculated = True

    monthly_cost = compute + storage + network
    yearly_cost = monthly_cost * 12

    if monthly_cost > 10000:
        status = "High Cost"
        recommendation = (
            "Review unused cloud resources, reduce "
            "unnecessary storage, and check cheaper "
            "service options."
        )
    elif monthly_cost > 5000:
        status = "Moderate Cost"
        recommendation = (
            "Review resource usage and consider "
            "scheduling non-production resources "
            "when they are not needed."
        )
    else:
        status = "Cost Under Control"
        recommendation = (
            "Continue monitoring costs and remove "
            "resources that are no longer required."
        )

    return render_template_string(
        HTML_PAGE,
        compute=compute,
        storage=storage,
        network=network,
        monthly_cost=round(monthly_cost, 2),
        yearly_cost=round(yearly_cost, 2),
        status=status,
        recommendation=recommendation,
        calculated=calculated
    )


if __name__ == "__main__":
    app.run(debug=True)
