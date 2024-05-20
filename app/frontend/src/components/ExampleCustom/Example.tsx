import styles from "./Example.module.css";

interface Props {
    title: string;
    text: string;
    value: string;
    icon: string;
    onClick: (value: string) => void;
}

export const Example = ({ text, value,title, icon, onClick }: Props) => {
    return (
        <div className={styles.example} onClick={() => onClick(value)}>
            <div className={styles.exampleBr}></div>
            <div className={styles.exampleValue}>{value}</div>
        </div>
    );
};
