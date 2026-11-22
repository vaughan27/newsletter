import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api/client";
import type { Role, User } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Modal } from "../components/Modal";
import { formatDateTime } from "../lib";

function UserForm({
  user,
  onClose,
  onSaved,
}: {
  user: User | null; // null = create
  onClose: () => void;
  onSaved: () => void;
}) {
  const { user: me } = useAuth();
  const isSelf = user !== null && me?.id === user.id;
  const [username, setUsername] = useState(user?.username ?? "");
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>(user?.role ?? "manager");
  const [active, setActive] = useState(user?.is_active ?? true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (user) {
        await api.patch(`/users/${user.id}`, {
          username,
          full_name: fullName,
          role,
          is_active: active,
          ...(password ? { password } : {}),
        });
      } else {
        await api.post("/users", { username, full_name: fullName, password, role, is_active: active });
      }
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't save the user.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title={user ? "Edit user" : "New user"} onClose={onClose}>
      <form className="form" onSubmit={onSubmit}>
        {error && <div className="alert alert--error">{error}</div>}
        <label className="field">
          <span>Full name</span>
          <input value={fullName} onChange={(e) => setFullName(e.target.value)} maxLength={120} required autoFocus />
        </label>
        <label className="field">
          <span>Username</span>
          <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="off" required />
          <small>Letters, numbers, dot, dash or underscore. Used to sign in.</small>
        </label>
        <label className="field">
          <span>{user ? "New password (leave blank to keep)" : "Password"}</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            minLength={8}
            required={!user}
          />
          <small>At least 8 characters.</small>
        </label>
        <label className="field">
          <span>Role</span>
          <select value={role} onChange={(e) => setRole(e.target.value as Role)} disabled={isSelf}>
            <option value="manager">Manager – upload newsletters, view dashboard</option>
            <option value="admin">Admin – everything, plus edit/delete and users</option>
          </select>
        </label>
        <label className="check">
          <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} disabled={isSelf} />
          <span>Account is active (can sign in)</span>
        </label>
        <div className="modal__actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn--primary" disabled={busy}>
            {busy ? "Saving…" : user ? "Save changes" : "Create user"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export function UsersPage() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState<User[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<{ user: User | null } | null>(null);

  const load = useCallback(() => {
    api
      .get<User[]>("/users")
      .then(setUsers)
      .catch((e: Error) => setError(e.message));
  }, []);
  useEffect(load, [load]);

  async function remove(u: User) {
    if (!window.confirm(`Delete user “${u.username}”? This can't be undone.`)) return;
    try {
      await api.del(`/users/${u.id}`);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't delete the user.");
    }
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Users</h1>
          <p className="muted">Staff who can sign in. Readers never need an account.</p>
        </div>
        <button className="btn btn--primary" onClick={() => setForm({ user: null })}>
          New user
        </button>
      </div>
      {error && <div className="alert alert--error">{error}</div>}
      <section className="panel">
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Username</th>
                <th>Role</th>
                <th>Status</th>
                <th>Last sign in</th>
                <th className="num">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users?.map((u) => (
                <tr key={u.id}>
                  <td>
                    <strong>{u.full_name}</strong> {u.id === me?.id && <span className="muted">(you)</span>}
                  </td>
                  <td>{u.username}</td>
                  <td>
                    <span className={`badge badge--${u.role}`}>{u.role}</span>
                  </td>
                  <td>{u.is_active ? "Active" : <span className="muted">Disabled</span>}</td>
                  <td>{formatDateTime(u.last_login_at)}</td>
                  <td className="num">
                    <div className="row-actions">
                      <button className="btn btn--sm" onClick={() => setForm({ user: u })}>
                        Edit
                      </button>
                      <button className="btn btn--sm btn--danger" disabled={u.id === me?.id} onClick={() => remove(u)}>
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {form && (
        <UserForm
          user={form.user}
          onClose={() => setForm(null)}
          onSaved={() => {
            setForm(null);
            load();
          }}
        />
      )}
    </>
  );
}
