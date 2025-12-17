import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook for always-on voice chat with AI tutor
 * Handles continuous speech recognition and text-to-speech
 */
export const useVoiceChat = (onTranscript, isEnabled = true) => {
    const [isListening, setIsListening] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [error, setError] = useState(null);
    const [isSupported, setIsSupported] = useState(false);

    const recognitionRef = useRef(null);
    const synthRef = useRef(null);
    const isUnmountedRef = useRef(false);

    // Use Refs for mutable state to avoid Effect re-runs
    const isEnabledRef = useRef(isEnabled);
    const isSpeakingRef = useRef(false); // Ref for internal logic
    const onTranscriptRef = useRef(onTranscript);

    // Sync refs
    useEffect(() => { isEnabledRef.current = isEnabled; }, [isEnabled]);
    useEffect(() => { onTranscriptRef.current = onTranscript; }, [onTranscript]);
    // Sync isSpeaking state with ref
    useEffect(() => { isSpeakingRef.current = isSpeaking; }, [isSpeaking]);

    // Check browser support on mount
    useEffect(() => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const SpeechSynthesis = window.speechSynthesis;

        if (SpeechRecognition && SpeechSynthesis) {
            setIsSupported(true);
            synthRef.current = SpeechSynthesis;
        } else {
            setIsSupported(false);
            setError('Voice chat is not supported in this browser. Please use Chrome or Edge.');
        }
    }, []);

    // Initialize continuous speech recognition with real-time transcription
    const initializeVoiceMode = useCallback(async () => {
        console.log('🎤 initializeVoiceMode called', {
            isSupported,
            isEnabled: isEnabledRef.current,
            isUnmounted: isUnmountedRef.current
        });

        if (!isSupported) return;
        if (!isEnabledRef.current || isUnmountedRef.current) return;

        try {
            // Request microphone permission first
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();

            recognition.lang = 'en-US';
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.maxAlternatives = 1;

            let silenceTimer = null;
            let currentTranscript = '';

            recognition.onstart = () => {
                console.log('✅ Voice recognition started');
                setIsListening(true);
                setError(null);
            };

            recognition.onresult = (event) => {
                let interimTranscript = '';
                let finalTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript + ' ';
                    } else {
                        interimTranscript += transcript;
                    }
                }

                if (finalTranscript) currentTranscript += finalTranscript;

                const displayTranscript = currentTranscript + interimTranscript;
                if (displayTranscript.trim()) {
                    onTranscriptRef.current?.(displayTranscript.trim(), false);
                }

                if (silenceTimer) clearTimeout(silenceTimer);

                if (currentTranscript.trim()) {
                    silenceTimer = setTimeout(() => {
                        console.log('🔕 Silence detected, submitting:', currentTranscript);
                        onTranscriptRef.current?.(currentTranscript.trim(), true);
                        currentTranscript = '';
                    }, 1200); // Reduced to 1200ms for snappier response
                }
            };

            recognition.onerror = (event) => {
                if (event.error === 'no-speech' || event.error === 'aborted') return;
                console.error('❌ Speech recognition error:', event.error);
                if (event.error === 'not-allowed') {
                    setError('Microphone access denied.');
                    setIsListening(false);
                }
            };

            recognition.onend = () => {
                console.log('🔴 Voice recognition ended');
                if (silenceTimer) clearTimeout(silenceTimer);

                // Check deps using Refs to decide whether to restart
                if (!isSpeakingRef.current && isEnabledRef.current && !isUnmountedRef.current) {
                    console.log('🔄 Auto-restarting recognition...');
                    try {
                        recognition.start();
                    } catch (e) {
                        console.log('⚠️ Restart prevented:', e.message);
                    }
                } else {
                    console.log('Not restarting:', {
                        speaking: isSpeakingRef.current,
                        enabled: isEnabledRef.current
                    });
                    setIsListening(false);
                }
            };

            recognitionRef.current = recognition;
            recognition.start();

        } catch (error) {
            console.error('❌ Error initializing voice mode:', error);
            setError(`Failed to start: ${error.message}`);
            setIsListening(false);
        }
    }, [isSupported]); // Removed isEnabled/isSpeaking dependencies to prevent restart loops

    // Pause listening (used before speaking)
    const pauseListening = useCallback(() => {
        if (recognitionRef.current) {
            try {
                // validation: usage of abort() instead of stop() to prevent "listening to self"
                recognitionRef.current.abort();
                // setIsListening(false); 
            } catch (error) {
                console.error('Error pausing:', error);
            }
        }
    }, []);

    // Resume listening (used after speaking)
    const resumeListening = useCallback(() => {
        // Check refs!
        if (recognitionRef.current && !isSpeakingRef.current && isEnabledRef.current) {
            try {
                recognitionRef.current.start();
            } catch (error) {
                console.error('Error resuming:', error);
            }
        }
    }, []);

    // Speak text using text-to-speech
    const speak = useCallback((text, onBoundary) => {
        if (!synthRef.current || !text) return;

        // SANITIZE TEXT FOR SPEECH:
        // Replace <sup> with "raised to the power of"
        let speakText = text.replace(/<sup>(.*?)<\/sup>/gi, ' raised to the power of $1 ');
        // Replace <sub> with "base"
        speakText = speakText.replace(/<sub>(.*?)<\/sub>/gi, ' base $1 ');

        // Remove markdown images entirely for speech: ![alt](url) -> ""
        speakText = speakText.replace(/!\[([^\]]*)\]\([^)]+\)/g, '');
        // Remove raw URLs
        speakText = speakText.replace(/https?:\/\/\S+/g, '');

        // Strip other HTML tags for speech
        speakText = speakText.replace(/<[^>]*>/g, ' ');
        // Normalize whitespace
        speakText = speakText.replace(/\s+/g, ' ').trim();

        console.log('🔊 Speak requested:', speakText);

        // Update Refs AND State
        isSpeakingRef.current = true;
        setIsSpeaking(true);

        // Pause listening
        pauseListening();

        // Cancel existing
        synthRef.current.cancel();

        const utterance = new SpeechSynthesisUtterance(speakText);
        utterance.lang = 'en-US';
        utterance.rate = 1.1; // Increased for better efficiency (was 0.9)

        if (onBoundary) {
            utterance.onboundary = (event) => {
                if (event.name === 'word') onBoundary(event.charIndex);
            };
        }

        utterance.onend = () => {
            console.log('🔊 Speech ended');
            isSpeakingRef.current = false;
            setIsSpeaking(false);
            if (onBoundary) onBoundary(-1);

            // Resume listening
            setTimeout(() => {
                resumeListening();
            }, 100); // Reduced delay for faster turnaround
        };

        utterance.onerror = (event) => {
            console.error('Speech error:', event);
            isSpeakingRef.current = false;
            setIsSpeaking(false);
            if (onBoundary) onBoundary(-1);
            resumeListening();
        };

        synthRef.current.speak(utterance);
    }, [pauseListening, resumeListening]);

    // Cleanup
    useEffect(() => {
        isUnmountedRef.current = false;
        if (isEnabled && isSupported) {
            initializeVoiceMode();
        }
        return () => {
            // We don't necessarily want to set unmounted to true on every dep change if we had deps,
            // but now initializeVoiceMode has few deps.
            // Actually, if 'isEnabled' toggles, this clean up runs.
            // If 'isSupported' changes (rare), it runs.

            if (!isEnabled) {
                // If checking purely on unmount, we need a separate effect.
                // But here we want to stop if disabled.
                if (recognitionRef.current) recognitionRef.current.abort();
                if (synthRef.current) synthRef.current.cancel();
                setIsListening(false);
                setIsSpeaking(false);
                isSpeakingRef.current = false;
            }
        };
    }, [isEnabled, isSupported, initializeVoiceMode]);

    // Separate unmount cleanup
    useEffect(() => {
        return () => {
            isUnmountedRef.current = true;
            if (recognitionRef.current) recognitionRef.current.abort();
            if (synthRef.current) synthRef.current.cancel();
        };
    }, []);

    return {
        isListening,
        isSpeaking,
        isSupported,
        error,
        speak,
        stopSpeaking: useCallback(() => {
            if (synthRef.current) synthRef.current.cancel();
            isSpeakingRef.current = false;
            setIsSpeaking(false);
            // Don't auto-resume if we're stopping everything? 
            // Logic in component handles "Stop Voice Chat" toggling isEnabled to false.
        }, []),
        pauseListening,
        resumeListening,
        startListening: initializeVoiceMode,
        stopListening: useCallback(() => {
            if (recognitionRef.current) recognitionRef.current.abort();
            setIsListening(false);
        }, [])
    };
};
