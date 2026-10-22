import { useEffect, useState } from "react";
import Button from "../../components/Button";
import Card from "../../components/Card";
import Input from "../../components/Input";
import Navbar from "../../components/Navbar";
import { getCurrentUserId } from "../../utils/auth";
import { getProfile, updateProfile, uploadProfileImage } from "../../services/userService";

export default function Profile() {
	const [form, setForm] = useState({
		bio: "",
		location: "",
		timezone: "",
		preferred_languages: ""
	});
	const [stats, setStats] = useState({
		name: "",
		user_id: null,
		identity_confidence_score: 0,
		trust_score: 0,
		email: "",
		phone: "",
		location: "",
		timezone: "",
		preferred_languages: "",
		created_at: "",
		last_login_at: "",
		skills_offered: [],
		skills_desired: [],
		email_verified: false,
		phone_verified: false
	});
	const [imageUrl, setImageUrl] = useState("");
	const [uploading, setUploading] = useState(false);
	const [message, setMessage] = useState("");
	const [error, setError] = useState("");

	useEffect(() => {
		const userId = getCurrentUserId();
		if (!userId) return;

		getProfile(userId)
			.then((res) => {
				const profile = res.data || {};
				setForm({
					bio: profile.bio || "",
					location: profile.location || "",
					timezone: profile.timezone || "",
					preferred_languages: profile.preferred_languages || ""
				});
				setStats({
					name: profile.name || "",
					user_id: profile.user_id || userId,
					identity_confidence_score: Number(profile.identity_confidence_score || 0),
					trust_score: Number(profile.trust_score || 0),
					email: profile.email || "",
					phone: profile.phone || "",
					location: profile.location || "",
					timezone: profile.timezone || "",
					preferred_languages: profile.preferred_languages || "",
					created_at: profile.created_at || "",
					last_login_at: profile.last_login_at || "",
					skills_offered: Array.isArray(profile.skills_offered) ? profile.skills_offered : [],
					skills_desired: Array.isArray(profile.skills_desired) ? profile.skills_desired : [],
					email_verified: Boolean(profile.email_verified),
					phone_verified: Boolean(profile.phone_verified)
				});

				const storedImage = localStorage.getItem(`profile_photo_${userId}`) || "";
				setImageUrl(storedImage);
			})
			.catch((err) => {
				const detail = err?.response?.data?.detail;
				setError(typeof detail === "string" ? detail : "Unable to load profile.");
			});
	}, []);

	const saveProfile = async (e) => {
		e.preventDefault();
		const userId = getCurrentUserId();
		if (!userId) {
			setMessage("Session expired. Please login again.");
			return;
		}

		try {
			setMessage("");
			setError("");
			await updateProfile({
				user_id: userId,
				...form,
				preferred_languages: form.preferred_languages
			});
			setMessage("Profile updated successfully.");
		} catch (err) {
			const detail = err?.response?.data?.detail;
			setError(typeof detail === "string" ? detail : "Unable to save profile right now.");
		}
	};

	const handlePhotoUpload = async (e) => {
		const userId = getCurrentUserId();
		const file = e.target.files?.[0];
		if (!userId || !file) return;

		try {
			setUploading(true);
			setError("");
			setMessage("");
			const res = await uploadProfileImage(userId, file);
			const url = res.data?.image_url || "";

			if (url) {
				setImageUrl(url);
				localStorage.setItem(`profile_photo_${userId}`, url);
			}

			setMessage("Profile photo updated.");
		} catch (err) {
			const detail = err?.response?.data?.detail;
			setError(typeof detail === "string" ? detail : "Unable to upload profile photo.");
		} finally {
			setUploading(false);
		}
	};

	const formatDate = (value) => {
		if (!value) return "-";
		const d = new Date(value);
		return Number.isNaN(d.getTime()) ? "-" : d.toLocaleString();
	};

	return (
		<div className="page-shell">
			<Navbar />
			<main className="page-container" style={{ width: "min(900px, 92vw)" }}>
				<Card variant="glass" className="animate-float-in">
					<h1 style={{ margin: 0, fontSize: 34 }}>My Profile</h1>
					<p className="muted-text" style={{ marginTop: 8 }}>View everything stored for your account and keep your details up to date.</p>

					<div className="profile-header">
						<div className="profile-avatar-wrap">
							{imageUrl ? (
								<img src={imageUrl} alt="Profile" className="profile-avatar" />
							) : (
								<div className="profile-avatar profile-avatar--placeholder">
									{(stats.name || stats.email || "U").charAt(0).toUpperCase()}
								</div>
							)}
							<label className="profile-photo-btn">
								{uploading ? "Uploading..." : "Upload Photo"}
								<input type="file" accept="image/jpeg,image/png" onChange={handlePhotoUpload} hidden disabled={uploading} />
							</label>
						</div>
						<div className="profile-meta">
							<h3>{stats.name || "User"}</h3>
							<p>{stats.email || "-"}</p>
							<p className="muted-text">User ID: {stats.user_id || "-"}</p>
						</div>
					</div>

					<div className="stats-grid stats-grid--3" style={{ marginTop: 14 }}>
						<Card className="stat-card">
							<p className="stat-card__label">Identity Confidence</p>
							<p className="stat-card__value">{stats.identity_confidence_score.toFixed(2)}</p>
						</Card>
						<Card className="stat-card">
							<p className="stat-card__label">Trust Score</p>
							<p className="stat-card__value">{stats.trust_score.toFixed(2)}</p>
						</Card>
						<Card className="stat-card">
							<p className="stat-card__label">Verification Status</p>
							<p className="stat-card__value" style={{ fontSize: 14, lineHeight: 1.4 }}>
								Email: {stats.email_verified ? "Verified" : "Not verified"}
								<br />
								Phone: {stats.phone_verified ? "Verified" : "Not verified"}
							</p>
						</Card>
					</div>

					<div className="profile-grid">
						<Card>
							<p className="section-title">Account Details</p>
							<div className="profile-list">
								<p><strong>Email:</strong> {stats.email || "-"}</p>
								<p><strong>Phone:</strong> {stats.phone || "-"}</p>
								<p><strong>Location:</strong> {stats.location || "-"}</p>
								<p><strong>Timezone:</strong> {stats.timezone || "-"}</p>
								<p><strong>Preferred Languages:</strong> {stats.preferred_languages || "-"}</p>
								<p><strong>Joined:</strong> {formatDate(stats.created_at)}</p>
								<p><strong>Last Login:</strong> {formatDate(stats.last_login_at)}</p>
							</div>
						</Card>

						<Card>
							<p className="section-title">Skills Snapshot</p>
							<div className="profile-skill-block">
								<p className="profile-skill-title">Offered Skills</p>
								<div className="skill-tags">
									{stats.skills_offered.length ? stats.skills_offered.map((s) => (
										<span key={`offered-${s.id}`} className="skill-tag">{s.skill_name} · {s.proficiency_level}</span>
									)) : <span className="muted-text">No offered skills yet</span>}
								</div>
							</div>
							<div className="profile-skill-block">
								<p className="profile-skill-title">Desired Skills</p>
								<div className="skill-tags">
									{stats.skills_desired.length ? stats.skills_desired.map((s) => (
										<span key={`desired-${s.id}`} className="skill-tag">{s.skill_name} · {s.proficiency_level}</span>
									)) : <span className="muted-text">No desired skills yet</span>}
								</div>
							</div>
						</Card>

					</div>

					<form onSubmit={saveProfile} className="form-grid">
						<Input
							label="Bio"
							placeholder="Tell others what you teach and what you want to learn"
							value={form.bio}
							onChange={(e) => setForm({ ...form, bio: e.target.value })}
						/>
						<Input
							label="Location"
							placeholder="City, Country"
							value={form.location}
							onChange={(e) => setForm({ ...form, location: e.target.value })}
						/>
						<Input
							label="Timezone"
							placeholder="Asia/Kolkata"
							value={form.timezone}
							onChange={(e) => setForm({ ...form, timezone: e.target.value })}
						/>
						<Input
							label="Preferred Languages"
							placeholder="English, Hindi"
							value={form.preferred_languages}
							onChange={(e) => setForm({ ...form, preferred_languages: e.target.value })}
						/>

						{message ? <p className="status-text success">{message}</p> : null}
						{error ? <p className="status-text error">{error}</p> : null}

						<Button type="submit">Save Changes</Button>
					</form>
				</Card>
			</main>
		</div>
	);
}
