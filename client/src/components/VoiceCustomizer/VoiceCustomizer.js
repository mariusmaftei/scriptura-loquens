import React, { useState, useEffect } from "react";
import styles from "./VoiceCustomizer.module.css";
import Button from "../Button/Button";

const VoiceCustomizer = ({
  characters = [],
  voiceSettings = {},
  availableVoices = [],
  language = "en",
  onVoiceChange,
  onSpeedChange,
  onPreview,
  onSave,
  previewingVoice,
}) => {
  const [localSettings, setLocalSettings] = useState(voiceSettings);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    setLocalSettings(voiceSettings);
  }, [voiceSettings]);

  const handleVoiceChange = (characterKey, voiceId) => {
    const newSettings = {
      ...localSettings,
      [characterKey]: {
        ...localSettings[characterKey],
        voice_id: voiceId,
      },
    };
    setLocalSettings(newSettings);
    setHasChanges(true);
    if (onVoiceChange) {
      onVoiceChange(characterKey, voiceId);
    }
  };

  const handleSpeedChange = (characterKey, speed) => {
    const newSettings = {
      ...localSettings,
      [characterKey]: {
        ...localSettings[characterKey],
        speed: parseFloat(speed),
      },
    };
    setLocalSettings(newSettings);
    setHasChanges(true);
    if (onSpeedChange) {
      onSpeedChange(characterKey, speed);
    }
  };

  const handleSave = () => {
    if (onSave) {
      const withNames = {};
      for (const [key, s] of Object.entries(localSettings)) {
        const name =
          s?.voice_id &&
          availableVoices.find((v) => v.voice_id === s.voice_id)?.voice_name;
        withNames[key] = { ...s, voice_name: name || s.voice_name };
      }
      onSave(withNames);
      setHasChanges(false);
    }
  };

  const getCharacterKey = (role, characterName) => {
    return characterName ? `${role}_${characterName}` : role;
  };

  const getCharacterLabel = (role, characterName) => {
    if (role === "narrator") {
      return "Narrator";
    }
    return characterName || "Character";
  };

  const langPrefix = (language || "").split("-")[0].toLowerCase();
  let filteredVoices = availableVoices.filter((voice) => {
    const vPrefix = (voice.language_code || "").split("-")[0].toLowerCase();
    return vPrefix === langPrefix;
  });
  if (filteredVoices.length === 0 && availableVoices.length > 0) {
    filteredVoices = availableVoices;
  }

  if (characters.length === 0) {
    return (
      <div className={styles.empty}>
        <p>No characters detected. Process a PDF first.</p>
      </div>
    );
  }

  if (filteredVoices.length === 0) {
    return (
      <div className={styles.empty}>
        <p>
          No voices available. Check that your TTS provider (e.g. ElevenLabs)
          API key is set in server/.env and restart the server.
        </p>
      </div>
    );
  }

  return (
    <div className={styles.voiceCustomizer}>
      {onSave && (
        <div className={styles.header}>
          <h2 className={styles.title}>Voice Settings</h2>
          {hasChanges && (
            <Button variant="primary" size="sm" onClick={handleSave}>
              Save Changes
            </Button>
          )}
        </div>
      )}

      <div className={styles.charactersList}>
        {characters.map((character) => {
          const characterKey = getCharacterKey(
            character.role,
            character.character_name
          );
          const settings = localSettings[characterKey] || {
            voice_id: "",
            speed: 1.0,
          };

          return (
            <div key={characterKey} className={styles.characterCard}>
              <div className={styles.characterHeader}>
                <h3 className={styles.characterName}>
                  {getCharacterLabel(character.role, character.character_name)}
                </h3>
                {character.character_name && (
                  <span className={styles.roleBadge}>{character.role}</span>
                )}
              </div>

              <div className={styles.controls}>
                <div className={styles.controlGroup}>
                  <label className={styles.label}>Voice</label>
                  <select
                    className={styles.select}
                    value={settings.voice_id || ""}
                    onChange={(e) =>
                      handleVoiceChange(characterKey, e.target.value)
                    }
                  >
                    <option value="">Select a voice</option>
                    {filteredVoices.map((voice) => (
                      <option key={voice.voice_id} value={voice.voice_id}>
                        {voice.voice_name || voice.voice_id}
                      </option>
                    ))}
                  </select>
                </div>

                <div className={styles.controlGroup}>
                  <label className={styles.label}>
                    Speed: {settings.speed?.toFixed(1)}x
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="2"
                    step="0.1"
                    value={settings.speed || 1.0}
                    onChange={(e) =>
                      handleSpeedChange(characterKey, e.target.value)
                    }
                    className={styles.slider}
                  />
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onPreview?.(characterKey, settings)}
                  disabled={
                    !settings.voice_id || previewingVoice === characterKey
                  }
                >
                  {previewingVoice === characterKey ? "Playing..." : "Preview"}
                </Button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default VoiceCustomizer;
