import React from "react";
import { Link } from "react-router-dom";
import styles from "./HomePage.module.css";
import mainImage from "../../assets/images/main.png";

const HomePage = () => {
  return (
    <div className={styles.homePage}>
      <section className={styles.hero}>
        <div className={styles.imageContainer}>
          <img src={mainImage} alt="Bible" className={styles.bibleImage} />
        </div>
        <div className={styles.heroContent}>
          <h1 className={styles.heroTitle}>
            <span className={styles.heroTitleGradient}>Scriptura</span> Loquens
          </h1>
          <p className={styles.heroSubtitle}>
            Transformă textele biblice în narațiuni audio imersive, cu voci
            multiple, prin detectare automată de personaje și sinteză vocală
            naturală.
          </p>
          <div className={styles.heroActions}>
            <Link to="/biblioteca" className={styles.exploreButton}>
              Explorează documentele
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
