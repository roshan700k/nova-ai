import { useEffect, useState } from "react";
import {
  getAdminUsers,
  updateAdminUser,
  getAdminFeatures,
  updateAdminFeature,
  getAdminStats,
} from "../api/chatApi";

export default function AdminPanel() {
  const [users, setUsers] = useState([]);
  const [features, setFeatures] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      const [usersData, featuresData, statsData] = await Promise.all([
        getAdminUsers(),
        getAdminFeatures(),
        getAdminStats(),
      ]);
      setUsers(usersData);
      setFeatures(featuresData);
      setStats(statsData);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load admin data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const t = setTimeout(fetchData, 0);
    return () => clearTimeout(t);
  }, []);

  const toggleFeature = async (name, enabled) => {
    try {
      await updateAdminFeature(name, { name, enabled: !enabled });
      fetchData();
    } catch {
      alert("Failed to update feature");
    }
  };

  const updateUserRole = async (userId, role) => {
    try {
      await updateAdminUser(userId, { role });
      fetchData();
    } catch {
      alert("Failed to update user");
    }
  };

  if (loading) return <div className="loading-spinner" />;
  if (error) return <div className="error-fallback"><h2>Admin Error</h2><p>{error}</p></div>;

  return (
    <div className="admin-panel">
      <div className="section-title"><span>ADMIN PANEL</span></div>

      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-number">{stats.total_users}</div>
            <div className="stat-label">Total Users</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{stats.active_users}</div>
            <div className="stat-label">Active Users</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{stats.total_memories}</div>
            <div className="stat-label">Total Memories</div>
          </div>
        </div>
      )}

      <div className="admin-section">
        <div className="section-title"><span>FEATURES</span></div>
        {features.length === 0 && <div className="empty-note">No features configured</div>}
        {features.map((f) => (
          <div key={f.name} className="feature-item">
            <div className="feature-info">
              <div className="feature-name">{f.name}</div>
              <div className="feature-desc">{f.description}</div>
            </div>
            <button
              className={`feature-toggle ${f.enabled ? "enabled" : "disabled"}`}
              onClick={() => toggleFeature(f.name, f.enabled)}
            >
              {f.enabled ? "ON" : "OFF"}
            </button>
          </div>
        ))}
      </div>

      <div className="admin-section">
        <div className="section-title"><span>USERS</span></div>
        {users.map((u) => (
          <div key={u.id} className="user-item">
            <div className="user-info">
              <div className="user-name">{u.name}</div>
              <div className="user-email">{u.email}</div>
            </div>
            <div className="user-actions">
              <select
                value={u.role}
                onChange={(e) => updateUserRole(u.id, e.target.value)}
                className="role-select"
              >
                <option value="user">User</option>
                <option value="admin">Admin</option>
              </select>
              <span className={`user-status ${u.is_active ? "active" : "inactive"}`}>
                {u.is_active ? "Active" : "Inactive"}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
