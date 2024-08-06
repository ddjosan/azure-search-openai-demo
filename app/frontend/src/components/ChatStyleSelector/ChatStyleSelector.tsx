import * as React from "react";
import { useState } from "react";
import { Radio, RadioGroup } from "@fluentui/react-components";
import styles from "./ChatStyleSelector.module.css";
import { Brush, Scale } from "lucide-react";

export const ChatStyleSelector = () => {
  const [selectedValue, setSelectedValue] = useState("creative");

  const handleChange = (event: any) => {
    setSelectedValue(event.target.value);
    console.log(`Selected: ${event.target.value}`);
  };

  return (
    <>
        <span className={styles.customLabel}>Choose a conversation style</span>
        <RadioGroup layout="horizontal-stacked" onChange={handleChange} className={styles.customRadioGroup}>
            <Radio value="creative" label={<><Brush size={20} style={{marginRight:8}}/>Creative</>} className={`${styles.customRadio} ${selectedValue === "creative" ? styles.selected : ""}`}/>
            <Radio value="balanced" label={<><Scale size={20} style={{marginRight:8}}/>Balanced</>}  className={`${styles.customRadio} ${selectedValue === "balanced" ? styles.selected : ""}`}/>
        </RadioGroup>
    </>
  );
};