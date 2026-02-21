import React, { useEffect, useRef, useMemo } from "react";
import styles from "./ChunkViewer.module.css";

const isTitleChunk = (chunk) => {
  const chunkType = chunk.chunk_type || "verse";
  if (
    ["book_title", "chapter_number", "chapter_name", "section_title"].includes(
      chunkType
    )
  ) {
    return true;
  }

  const text = (chunk.text || "").trim();
  if (!text) return false;

  if (chunk.role === "narrator") {
    if (
      text === text.toUpperCase() &&
      text.length < 20 &&
      !/^\d+[\s\.]/.test(text)
    ) {
      return true;
    }
    if (/^capitolul\s+\d+/i.test(text)) {
      return true;
    }

    const wordCount = text.split(/\s+/).length;
    const hasVerseNumber = /^\d+[\s\.]/.test(text);

    if (!hasVerseNumber && !/^\d+\./.test(text)) {
      const titlePatterns = [
        /^geneza\s*$/i,
        /^facerea\s+lumii$/i,
        /^lumina$/i,
        /^cerul$/i,
        /^pământul$/i,
        /^soarele/i,
        /^vieţuitoare/i,
      ];
      if (titlePatterns.some((re) => re.test(text))) {
        return true;
      }

      if (wordCount === 1 && text.length < 20) {
        return true;
      }

      if (wordCount <= 3 && text.length < 50) {
        return true;
      }

      if (
        wordCount > 3 &&
        wordCount <= 12 &&
        text.length < 100 &&
        !hasVerseNumber
      ) {
        const chapterNamePatterns = [/vremurile/i, /facerea/i, /până la/i];
        if (chapterNamePatterns.some((re) => re.test(text))) {
          return true;
        }
      }
    }
  }

  return false;
};

const parseReference = (ref) => {
  const parts = ref.trim().split(/\s+/);
  if (parts.length < 2) return null;

  const book = parts[0].replace(/\.$/, "");
  const versePart = parts.slice(1).join(" ");
  const verseMatch = versePart.match(/(\d+):(\d+)/);

  if (verseMatch) {
    return {
      book: book,
      chapter: parseInt(verseMatch[1]),
      verse: parseInt(verseMatch[2]),
      full: ref.trim(),
    };
  }
  return { book: book, full: ref.trim() };
};

const VerseReferences = ({ references }) => {
  if (!references || references.length === 0) return null;

  const handleReferenceClick = (ref) => {
    const parsed = parseReference(ref);
    if (parsed) {
      console.log("Navigate to:", parsed);
    }
  };

  return (
    <div className={styles.references}>
      {references.map((ref, idx) => {
        const parsed = parseReference(ref);
        return (
          <button
            key={idx}
            className={styles.referenceLink}
            onClick={(e) => {
              e.stopPropagation();
              handleReferenceClick(ref);
            }}
            title={`Navigate to ${ref}`}
          >
            {ref}
          </button>
        );
      })}
    </div>
  );
};

function buildGroups(chunks) {
  const groups = [];
  for (const chunk of chunks) {
    const chunkType = chunk.chunk_type || "verse";
    const verseNum = chunk.verse_num;
    const isVerseWithNum =
      chunkType === "verse" &&
      verseNum != null &&
      verseNum !== "" &&
      !isTitleChunk(chunk);

    if (isVerseWithNum && groups.length > 0) {
      const last = groups[groups.length - 1];
      const lastChunk = last.chunks[last.chunks.length - 1];
      if (
        last.verseNum === String(verseNum) &&
        last.chunkType === "verse" &&
        lastChunk.position + 1 === chunk.position
      ) {
        last.chunks.push(chunk);
        continue;
      }
    }
    groups.push({
      verseNum,
      chunkType,
      chunks: [chunk],
    });
  }
  return groups;
}

const ChunkViewer = ({
  chunks = [],
  selectedChunkId,
  playingChunkId,
  onChunkSelect,
  scrollContainerRef,
  customNarratorName = null,
  customVoiceActorName = null,
}) => {
  const groupRefs = useRef({});

  const groups = useMemo(() => buildGroups(chunks), [chunks]);

  const playingGroupFirstId = useMemo(() => {
    if (!playingChunkId) return null;
    for (const g of groups) {
      if (g.chunks.some((c) => c.id === playingChunkId)) {
        return g.chunks[0].id;
      }
    }
    return playingChunkId;
  }, [playingChunkId, groups]);

  const selectedGroupFirstId = useMemo(() => {
    if (!selectedChunkId) return null;
    for (const g of groups) {
      if (g.chunks.some((c) => c.id === selectedChunkId)) {
        return g.chunks[0].id;
      }
    }
    return selectedChunkId;
  }, [selectedChunkId, groups]);

  useEffect(() => {
    const refKey = playingGroupFirstId ?? playingChunkId;
    if (!refKey) return;
    const element = groupRefs.current[refKey];
    const container = scrollContainerRef?.current;

    if (element && container) {
      setTimeout(() => {
        const containerRect = container.getBoundingClientRect();
        const elementRect = element.getBoundingClientRect();
        const headerOffset = 80;
        const scrollOffset = 20;

        const elementTopRelative =
          elementRect.top - containerRect.top + container.scrollTop;
        const targetScrollTop =
          elementTopRelative - headerOffset - scrollOffset;

        container.scrollTo({
          top: Math.max(0, targetScrollTop),
          behavior: "smooth",
        });
      }, 200);
    } else if (element) {
      setTimeout(() => {
        element.scrollIntoView({
          behavior: "smooth",
          block: "center",
          inline: "nearest",
        });
      }, 200);
    }
  }, [playingChunkId, playingGroupFirstId, scrollContainerRef]);

  if (!chunks || chunks.length === 0) {
    return (
      <div className={styles.empty}>
        <p>Nu există segmente. Procesează un PDF pentru a vedea textul.</p>
      </div>
    );
  }

  const getRoleLabel = (role, characterName) => {
    if (role === "narrator")
      return customNarratorName ? `Narrator (${customNarratorName})` : null;
    const base = characterName || "Personaj";
    return customVoiceActorName ? `${base} (${customVoiceActorName})` : base;
  };

  const getRoleColor = (role, characterName) => {
    if (role === "narrator") return "narrator";
    const colors = ["character1", "character2", "character3", "character4"];
    const hash = characterName ? characterName.charCodeAt(0) : 0;
    return colors[hash % colors.length];
  };

  const hasPlayingChunk = playingChunkId !== null;

  return (
    <div className={styles.chunkViewer}>
      <div
        className={`${styles.chunksList} ${
          hasPlayingChunk ? styles.hasPlaying : ""
        }`}
      >
        {groups.map((group) => {
          const firstChunk = group.chunks[0];
          const refKey = firstChunk.id;
          const isGroupVerse =
            group.chunkType === "verse" &&
            group.verseNum != null &&
            group.verseNum !== "" &&
            group.chunks.length > 0 &&
            !isTitleChunk(firstChunk);

          const isSelected =
            selectedChunkId != null &&
            group.chunks.some((c) => c.id === selectedChunkId);
          const isPlaying =
            playingChunkId != null &&
            group.chunks.some((c) => c.id === playingChunkId);

          const handleClick = () => {
            onChunkSelect?.(firstChunk.id);
          };

          if (group.chunks.length === 1 && isTitleChunk(firstChunk)) {
            const chunk = firstChunk;
            const text = (chunk.text || "").trim();
            const chunkType = chunk.chunk_type || "verse";
            const isBookTitle =
              text === text.toUpperCase() &&
              text.length < 20 &&
              !/^\d+[\s\.]/.test(text);
            const isChapterNum = /^capitolul\s+\d+/i.test(text);

            let titleClass = styles.sectionTitle;
            if (chunkType === "book_title" || isBookTitle) {
              titleClass = `${styles.sectionTitle} ${styles.book_title}`;
            } else if (chunkType === "chapter_number" || isChapterNum) {
              titleClass = `${styles.sectionTitle} ${styles.chapter_number}`;
            } else {
              titleClass = `${styles.sectionTitle} ${styles.chapter_name}`;
            }

            return (
              <div
                key={chunk.id}
                ref={(el) => {
                  if (el) groupRefs.current[chunk.id] = el;
                }}
                className={`${styles.chunk} ${titleClass} ${
                  isSelected ? styles.selected : ""
                } ${isPlaying ? styles.playing : ""}`}
                onClick={() => onChunkSelect?.(chunk.id)}
              >
                <p className={styles.sectionTitleText}>{chunk.text}</p>
              </div>
            );
          }

          if (isGroupVerse) {
            const inlineText = group.chunks.map((c) => c.text).join(" ").trim();
            const firstWithRefs = group.chunks.find(
              (c) => c.references && c.references.length > 0
            );

            return (
              <div
                key={refKey}
                ref={(el) => {
                  if (el) groupRefs.current[refKey] = el;
                }}
                className={`${styles.chunk} ${styles.verseGroup} ${
                  isSelected ? styles.selected : ""
                } ${isPlaying ? styles.playing : ""}`}
                onClick={handleClick}
              >
                <div className={styles.verseRow}>
                  <span className={styles.verseNum}>{group.verseNum}</span>
                  <div className={styles.verseBody}>
                    <p className={styles.chunkText}>{inlineText}</p>
                    {firstWithRefs?.references?.length > 0 && (
                      <VerseReferences references={firstWithRefs.references} />
                    )}
                  </div>
                </div>
              </div>
            );
          }

          return group.chunks.map((chunk) => {
            const roleClass = getRoleColor(chunk.role, chunk.character_name);
            const roleLabel = getRoleLabel(chunk.role, chunk.character_name);
            const asSelected = selectedChunkId === chunk.id;
            const asPlaying = playingChunkId === chunk.id;

            return (
              <div
                key={chunk.id}
                ref={(el) => {
                  if (el) groupRefs.current[chunk.id] = el;
                }}
                className={`${styles.chunk} ${styles[roleClass]} ${
                  asSelected ? styles.selected : ""
                } ${asPlaying ? styles.playing : ""}`}
                onClick={() => onChunkSelect?.(chunk.id)}
              >
                <div className={styles.verseRow}>
                  <span className={styles.verseNumSpacer} />
                  <div className={styles.verseBody}>
                    {roleLabel && (
                      <span className={styles.characterLabel}>{roleLabel}</span>
                    )}
                    <p className={styles.chunkText}>{chunk.text}</p>
                    {chunk.references && chunk.references.length > 0 && (
                      <VerseReferences references={chunk.references} />
                    )}
                  </div>
                </div>
              </div>
            );
          });
        })}
      </div>
    </div>
  );
};

export default ChunkViewer;
