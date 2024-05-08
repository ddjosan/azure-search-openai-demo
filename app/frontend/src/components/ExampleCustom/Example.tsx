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
            <img
                src={icon}
                alt="Example"
                height='70px'
                width='70px'
            />
            <h2>{title}</h2>
            <div>{text}</div>
            <div className={styles.exampleBr}></div>
            <div className={styles.exampleValue}>{'"'+value+'"'}</div>
        </div>
    );
};
