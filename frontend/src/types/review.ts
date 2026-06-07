export type SceneMark = "none" | "review" | "done";

export type HighlightColor = "red" | "orange" | "yellow" | "green" | "blue";

export type TextHighlight = {
  id: string;
  start: number;
  end: number;
  color: HighlightColor;
  text: string;
};
