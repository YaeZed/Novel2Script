import { z } from "zod";

export const beatSchema = z.object({
  type: z.enum(["dialogue", "action", "direction"]),
  character: z.string().optional(),
  content: z.string(),
  parenthetical: z.string().optional(),
});

export const sceneSchema = z.object({
  number: z.number(),
  title: z.string(),
  source_chapter: z.number(),
  summary: z.string().optional(),
  beats: z.array(beatSchema).min(1),
});

export const actSchema = z.object({
  number: z.number(),
  title: z.string(),
  scenes: z.array(sceneSchema),
});

export const scriptSchema = z.object({
  title: z.string(),
  characters: z.array(
    z.object({
      name: z.string(),
      role: z.string().optional(),
      description: z.string().optional(),
    }),
  ),
  acts: z.array(actSchema).min(1),
});

export type ScriptDocument = z.infer<typeof scriptSchema>;

