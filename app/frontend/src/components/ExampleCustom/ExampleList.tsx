import { Example } from "./Example";
import example1Img from "../../assets/example1.png";
import example2Img from "../../assets/example2.png";
import example3Img from "../../assets/example3.png";
import styles from "./Example.module.css";

interface ExampleC {
    title: string,
    text: string,
    value: string,
    icon: string
}
const DEFAULT_EXAMPLES: ExampleC[] = [
    {
        title:'What we set out to do',
        text: 'Project documentation outlning our ojbectives and goals.',
        value: 'Go through project documentation and collect all project outputs, then select those that are focused at trainings and capacity builiding, and group them in three meaningful categories.',
        icon: example1Img
    },
    {
        title:'What we have done',
        text: 'Progress reports tracking our project execution.',
        value: 'Search the progress reports on developed digital products, compare the findings over 2022 to 2023, and speculate on trends.',
        icon: example2Img
    },
    {
        title:'Dimensions of impact',
        text: 'Key result indicators that measure our reach.',
        value: "Provide a comprehensive overview of all activities and results related to women's empowerment undertaken in 2023, and group these into a set of MECE categories.",
        icon: example3Img
    }
];

interface Props {
    onExampleClicked: (value: string) => void;
    useGPT4V?: boolean;
}

export const ExampleList = ({ onExampleClicked, useGPT4V }: Props) => {
    return (
        <div className={styles.examplesNavList}>
            {DEFAULT_EXAMPLES.map((question, i) => (
                <Example key={i} title={question.title} text={question.text} value={question.value} icon={question.icon} onClick={onExampleClicked} />
           ))}
        </div>
    );
};
