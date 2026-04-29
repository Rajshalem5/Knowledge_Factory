import { useState } from 'react';
import { questionsApi, type QuestionPublicView, type GenerateRequest } from '../api/questions';

export const useQuestion = () => {
  const [question, setQuestion] = useState<QuestionPublicView | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async (req: GenerateRequest = {}) => {
    setIsGenerating(true);
    setError(null);
    try {
      const q = await questionsApi.generate(req);
      setQuestion(q);
      return q;
    } catch (e: any) {
      setError(e.message || 'Failed to generate question');
      throw e;
    } finally {
      setIsGenerating(false);
    }
  };

  return { question, isGenerating, error, generate, setQuestion };
};
