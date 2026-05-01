import { useState } from "react";
import axios from "axios";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts/es6";

const COLORS = { passed: "#1D9E75", failed: "#E24B4A", skipped: "#BA7517" };

export default function App() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [framework, setFramework] = useState("playwright");

  async function handleUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setError("");
    setReport(null);

    try {
      const res = await axios.post(
        `https://testreport-pro-production.up.railway.app/upload/${framework}`,
        formData
      );
      setReport(res.data);
    } catch (err) {
      setError("Erreur lors de l'upload. Vérifie que l'API tourne et que le fichier est correct.");
    } finally {
      setLoading(false);
    }
  }

  const pieData = report ? [
    { name: "Passed", value: report.passed },
    { name: "Failed", value: report.failed },
    { name: "Skipped", value: report.skipped },
  ] : [];

  return (
    <div style={{ minHeight: "100vh", background: "#F5F7FA", fontFamily: "Arial, sans-serif" }}>

      <div style={{ background: "#1F5C99", padding: "16px 32px", display: "flex", alignItems: "center", gap: 12 }}>
        <span style={{ color: "white", fontSize: 22, fontWeight: "bold" }}>TestReport</span>
        <span style={{ color: "#7BC8F6", fontSize: 22, fontWeight: "bold" }}>Pro</span>
      </div>

      <div style={{ maxWidth: 900, margin: "40px auto", padding: "0 24px" }}>

        <div style={{ background: "white", borderRadius: 12, padding: 32, border: "1px solid #E0E0E0", marginBottom: 24 }}>
          <h2 style={{ margin: "0 0 16px", color: "#1A1A2E", fontSize: 20 }}>Importer vos résultats de tests</h2>

          <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
            {["playwright", "pytest", "cucumber"].map(f => (
              <button
                key={f}
                onClick={() => setFramework(f)}
                style={{
                  padding: "8px 20px", borderRadius: 8, border: "none", cursor: "pointer", fontSize: 14, fontWeight: "bold",
                  background: framework === f ? "#1F5C99" : "#E8F0FB",
                  color: framework === f ? "white" : "#1F5C99"
                }}
              >
                {f === "playwright" ? "Playwright (JSON)" : f === "pytest" ? "Pytest (XML)" : "Cucumber (JSON)"}
              </button>
            ))}
          </div>

          <input type="file" accept={framework === "pytest" ? ".xml" : ".json"} onChange={handleUpload} style={{ fontSize: 14 }} />
          {loading && <p style={{ color: "#1F5C99", marginTop: 12 }}>Analyse en cours...</p>}
          {error && <p style={{ color: "#E24B4A", marginTop: 12 }}>{error}</p>}
        </div>

        {report && (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 24 }}>
              {[
                { label: "Total", value: report.total, color: "#1F5C99" },
                { label: "Passed", value: report.passed, color: "#1D9E75" },
                { label: "Failed", value: report.failed, color: "#E24B4A" },
                { label: "Taux de succès", value: `${report.success_rate}%`, color: "#1F5C99" },
              ].map(({ label, value, color }) => (
                <div key={label} style={{ background: "white", borderRadius: 12, padding: "20px 16px", border: "1px solid #E0E0E0", textAlign: "center" }}>
                  <div style={{ fontSize: 28, fontWeight: "bold", color }}>{value}</div>
                  <div style={{ fontSize: 13, color: "#888", marginTop: 4 }}>{label}</div>
                </div>
              ))}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
              <div style={{ background: "white", borderRadius: 12, padding: 24, border: "1px solid #E0E0E0" }}>
                <h3 style={{ margin: "0 0 16px", fontSize: 15, color: "#1A1A2E" }}>Répartition des tests</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                      {pieData.map((entry) => (
                        <Cell key={entry.name} fill={COLORS[entry.name.toLowerCase()]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div style={{ background: "white", borderRadius: 12, padding: 24, border: "1px solid #E0E0E0" }}>
                <h3 style={{ margin: "0 0 16px", fontSize: 15, color: "#1A1A2E" }}>Résultats par statut</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={pieData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value">
                      {pieData.map((entry) => (
                        <Cell key={entry.name} fill={COLORS[entry.name.toLowerCase()]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div style={{ background: "white", borderRadius: 12, padding: 24, border: "1px solid #E0E0E0" }}>
              <h3 style={{ margin: "0 0 16px", fontSize: 15, color: "#1A1A2E" }}>Détail des tests</h3>
              {report.tests.map((test, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 0", borderBottom: i < report.tests.length - 1 ? "1px solid #F0F0F0" : "none" }}>
                  <span style={{ background: COLORS[test.status] || "#888", color: "white", borderRadius: 6, padding: "2px 10px", fontSize: 12, fontWeight: "bold", minWidth: 60, textAlign: "center" }}>
                    {test.status}
                  </span>
                  <span style={{ flex: 1, fontSize: 14, color: "#1A1A2E" }}>{test.name}</span>
                  <span style={{ fontSize: 12, color: "#888" }}>{test.duration_ms}ms</span>
                  {test.error_message && (
                    <span style={{ fontSize: 12, color: "#E24B4A", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {test.error_message}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}