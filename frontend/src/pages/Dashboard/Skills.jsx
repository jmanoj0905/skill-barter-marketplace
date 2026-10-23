import { useState } from "react";
import Button from "../../components/Button";
import Card from "../../components/Card";
import Input from "../../components/Input";
import Navbar from "../../components/Navbar";
import { getCurrentUserId } from "../../utils/auth";
import { useEffect } from "react";
import { createSkill, deleteSkill, getSkills, suggestSkills, updateSkill } from "../../services/skillService";

export default function Skills() {
  const [skill, setSkill] = useState("");
  const [message, setMessage] = useState("");
  const [skillType, setSkillType] = useState("offered");
  const [level, setLevel] = useState("intermediate");
  const [offeredSkills, setOfferedSkills] = useState([]);
  const [desiredSkills, setDesiredSkills] = useState([]);
  const [skillSuggestions, setSkillSuggestions] = useState([]);
  const [editingId, setEditingId] = useState(null);

  const loadSkills = () => {
    const userId = getCurrentUserId();
    if (!userId) return;

    getSkills(userId)
      .then((res) => {
        setOfferedSkills(Array.isArray(res.data?.offered) ? res.data.offered : []);
        setDesiredSkills(Array.isArray(res.data?.desired) ? res.data.desired : []);
      })
      .catch(() => {});
  };

  useEffect(() => {
    loadSkills();
  }, []);

  useEffect(() => {
    const q = skill.trim();
    if (q.length < 2) {
      setSkillSuggestions([]);
      return;
    }

    suggestSkills(q)
      .then((res) => setSkillSuggestions(Array.isArray(res.data) ? res.data : []))
      .catch(() => setSkillSuggestions([]));
  }, [skill]);

  const addSkill = async (e) => {
    e.preventDefault();
    const userId = getCurrentUserId();

    if (!userId) {
      setMessage("Session expired. Please login again.");
      return;
    }

    try {
      setMessage("");
      const payload = {
        user_id: userId,
        skill_name: skill,
        skill_type: skillType,
        proficiency_level: level
      };

      if (editingId) {
        await updateSkill(editingId, payload);
        setMessage("Skill updated successfully.");
      } else {
        await createSkill(payload);
        setMessage("Skill added successfully.");
      }

      setSkill("");
      setEditingId(null);
      loadSkills();
    } catch {
      setMessage("Could not save skill right now.");
    }
  };

  const startEdit = (skillItem, type) => {
    setEditingId(skillItem.id);
    setSkill(skillItem.skill_name || "");
    setSkillType(type);
    setLevel(skillItem.proficiency_level || "intermediate");
  };

  const removeSkill = async (skillId) => {
    const userId = getCurrentUserId();
    if (!userId) return;

    try {
      await deleteSkill(skillId, userId);
      setMessage("Skill deleted.");
      loadSkills();
    } catch {
      setMessage("Could not delete this skill.");
    }
  };

  return (
    <div className="page-shell">
      <Navbar />
      <main className="page-container" style={{ width: "min(980px, 92vw)" }}>
        <Card variant="glass" className="animate-float-in">
          <h1 style={{ margin: 0, fontSize: 34 }}>Manage Skills</h1>
          <p className="muted-text" style={{ marginTop: 8 }}>
            Add what you can teach or what you want to learn.
          </p>

          <form onSubmit={addSkill} className="skill-form">
            <Input
              className=""
              placeholder="e.g., React, UI Design, Public Speaking"
              value={skill}
              onChange={(e) => setSkill(e.target.value)}
              required
            />
            <select
              value={skillType}
              onChange={(e) => setSkillType(e.target.value)}
              className="ui-select"
            >
              <option value="offered">Offered</option>
              <option value="desired">Desired</option>
            </select>
            <select
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              className="ui-select"
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
              <option value="expert">Expert</option>
            </select>
            <Button type="submit" className="sm:w-auto">
              {editingId ? "Update Skill" : "Add Skill"}
            </Button>
          </form>

          {skillSuggestions.length > 0 ? (
            <div className="suggestion-list">
              {skillSuggestions.map((item) => (
                <button
                  key={`${item.id || item.skill_name}`}
                  type="button"
                  className="suggestion-chip"
                  onClick={() => setSkill(item.skill_name || "")}
                >
                  {item.skill_name}
                </button>
              ))}
            </div>
          ) : null}

          {message ? <p className="status-text success">{message}</p> : null}

          <div className="skill-columns">
            <div>
              <h3 className="section-title">Skills Offered</h3>
              <div className="skill-list">
                {offeredSkills.map((item) => (
                  <div key={`offered-${item.id}`} className="skill-row">
                    <span className="skill-tag">{item.skill_name} · {item.proficiency_level}</span>
                    <div className="skill-row__actions">
                      <Button variant="secondary" onClick={() => startEdit(item, "offered")}>Edit</Button>
                      <Button variant="ghost" onClick={() => removeSkill(item.id)}>Delete</Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="section-title">Skills Desired</h3>
              <div className="skill-list">
                {desiredSkills.map((item) => (
                  <div key={`desired-${item.id}`} className="skill-row">
                    <span className="skill-tag">{item.skill_name} · {item.proficiency_level}</span>
                    <div className="skill-row__actions">
                      <Button variant="secondary" onClick={() => startEdit(item, "desired")}>Edit</Button>
                      <Button variant="ghost" onClick={() => removeSkill(item.id)}>Delete</Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>
      </main>
    </div>
  );
}