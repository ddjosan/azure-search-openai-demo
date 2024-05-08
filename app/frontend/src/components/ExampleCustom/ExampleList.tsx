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
        value: 'List all UNDP Serbia projects related to dealing with climate change.',
        icon: example1Img
    },
    {
        title:'What we have done',
        text: 'Progress reports tracking our project execution.',
        value: 'List all activities related to emerging technologies realized in 2023.',
        icon: example2Img
    },
    {
        title:'Dimensions of impact',
        text: 'Key result indicators that measure our reach.',
        value: "How many vulnerable individuals has UNDP Serbia's projects reached in 2023?",
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
