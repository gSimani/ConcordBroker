/**
 * usePropertyNotes Hook - Complete Supabase Integration
 * Provides property notes management with real-time updates
 * Part of ConcordBroker 100% Supabase Integration
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { supabase } from '@/lib/supabase';
import { useAuth } from './use-auth';
import { useToast } from '@/components/ui/use-toast';

// Types for property notes
export interface PropertyNote {
  id: string;
  user_id: string;
  parcel_id: string;
  county?: string;
  title?: string;
  notes: string;
  tags: string[];
  is_private: boolean;
  note_type: 'general' | 'investment' | 'contact' | 'reminder' | 'analysis';
  created_at: string;
  updated_at: string;
}

export interface PropertyNotesState {
  notesByProperty: Map<string, PropertyNote[]>;
  loading: boolean;
  error: string | null;
  totalCount: number;
}

export interface AddNoteParams {
  parcelId: string;
  county?: string;
  title?: string;
  notes: string;
  tags?: string[];
  isPrivate?: boolean;
  noteType?: PropertyNote['note_type'];
}

export interface UpdateNoteParams {
  title?: string;
  notes?: string;
  tags?: string[];
  isPrivate?: boolean;
  noteType?: PropertyNote['note_type'];
}

/**
 * Custom hook for managing property notes
 * Features:
 * - Real-time Supabase subscriptions
 * - Property-specific note grouping
 * - Full CRUD operations with optimistic updates
 * - Tag-based filtering and search
 * - Note type categorization
 */
export const usePropertyNotes = (parcelId?: string) => {
  const { user } = useAuth();
  const { toast } = useToast();

  // State management
  const [state, setState] = useState<PropertyNotesState>({
    notesByProperty: new Map(),
    loading: false,
    error: null,
    totalCount: 0,
  });

  // Get notes for specific property
  const propertyNotes = useMemo(() => {
    if (!parcelId) return [];
    return state.notesByProperty.get(parcelId) || [];
  }, [state.notesByProperty, parcelId]);

  // Get all notes across all properties
  const allNotes = useMemo(() => {
    const notes: PropertyNote[] = [];
    state.notesByProperty.forEach(propertyNotes => {
      notes.push(...propertyNotes);
    });
    return notes.sort((a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  }, [state.notesByProperty]);

  /**
   * Fetch notes for a specific property
   */
  const fetchPropertyNotes = useCallback(async (targetParcelId: string) => {
    if (!user?.id) return;

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const { data, error } = await supabase
        .from('property_notes')
        .select('*')
        .eq('user_id', user.id)
        .eq('parcel_id', targetParcelId)
        .order('created_at', { ascending: false });

      if (error) throw error;

      setState(prev => {
        const newNotesByProperty = new Map(prev.notesByProperty);
        newNotesByProperty.set(targetParcelId, data || []);

        return {
          ...prev,
          notesByProperty: newNotesByProperty,
          loading: false,
        };
      });

    } catch (error: any) {
      console.error('Error fetching property notes:', error);
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to fetch property notes',
        loading: false,
      }));

      toast({
        title: "Error Loading Notes",
        description: "Failed to load property notes. Please try again.",
        variant: "destructive",
      });
    }
  }, [user?.id, toast]);

  /**
   * Fetch all user notes (for dashboard/overview)
   */
  const fetchAllNotes = useCallback(async () => {
    if (!user?.id) return;

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const { data, error, count } = await supabase
        .from('property_notes')
        .select('*', { count: 'exact' })
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) throw error;

      // Group notes by property
      const notesByProperty = new Map<string, PropertyNote[]>();
      (data || []).forEach(note => {
        const existing = notesByProperty.get(note.parcel_id) || [];
        notesByProperty.set(note.parcel_id, [...existing, note]);
      });

      setState(prev => ({
        ...prev,
        notesByProperty,
        totalCount: count || 0,
        loading: false,
      }));

    } catch (error: any) {
      console.error('Error fetching all notes:', error);
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to fetch notes',
        loading: false,
      }));

      toast({
        title: "Error Loading Notes",
        description: "Failed to load your notes. Please try again.",
        variant: "destructive",
      });
    }
  }, [user?.id, toast]);

  /**
   * Add new note with optimistic update
   */
  const addNote = useCallback(async (params: AddNoteParams) => {
    if (!user?.id) {
      toast({
        title: "Authentication Required",
        description: "Please log in to add notes.",
        variant: "destructive",
      });
      return null;
    }

    // Optimistic update
    const optimisticNote: PropertyNote = {
      id: `temp-${Date.now()}`,
      user_id: user.id,
      parcel_id: params.parcelId,
      county: params.county,
      title: params.title,
      notes: params.notes,
      tags: params.tags || [],
      is_private: params.isPrivate ?? true,
      note_type: params.noteType || 'general',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setState(prev => {
      const newNotesByProperty = new Map(prev.notesByProperty);
      const existingNotes = newNotesByProperty.get(params.parcelId) || [];
      newNotesByProperty.set(params.parcelId, [optimisticNote, ...existingNotes]);

      return {
        ...prev,
        notesByProperty: newNotesByProperty,
        totalCount: prev.totalCount + 1,
      };
    });

    try {
      const { data, error } = await supabase
        .from('property_notes')
        .insert({
          user_id: user.id,
          parcel_id: params.parcelId,
          county: params.county,
          title: params.title,
          notes: params.notes,
          tags: params.tags || [],
          is_private: params.isPrivate ?? true,
          note_type: params.noteType || 'general',
        })
        .select()
        .single();

      if (error) throw error;

      // Replace optimistic note with real data
      setState(prev => {
        const newNotesByProperty = new Map(prev.notesByProperty);
        const existingNotes = newNotesByProperty.get(params.parcelId) || [];
        const updatedNotes = existingNotes.map(note =>
          note.id === optimisticNote.id ? data : note
        );
        newNotesByProperty.set(params.parcelId, updatedNotes);

        return {
          ...prev,
          notesByProperty: newNotesByProperty,
        };
      });

      toast({
        title: "Note Added",
        description: "Your note has been saved successfully.",
        variant: "default",
      });

      return data;

    } catch (error: any) {
      console.error('Error adding note:', error);

      // Revert optimistic update
      setState(prev => {
        const newNotesByProperty = new Map(prev.notesByProperty);
        const existingNotes = newNotesByProperty.get(params.parcelId) || [];
        const updatedNotes = existingNotes.filter(note => note.id !== optimisticNote.id);

        if (updatedNotes.length === 0) {
          newNotesByProperty.delete(params.parcelId);
        } else {
          newNotesByProperty.set(params.parcelId, updatedNotes);
        }

        return {
          ...prev,
          notesByProperty: newNotesByProperty,
          totalCount: prev.totalCount - 1,
        };
      });

      toast({
        title: "Error Adding Note",
        description: "Failed to add note. Please try again.",
        variant: "destructive",
      });

      return null;
    }
  }, [user?.id, toast]);

  /**
   * Update existing note
   */
  const updateNote = useCallback(async (
    noteId: string,
    updates: UpdateNoteParams
  ) => {
    if (!user?.id) return false;

    // Find the note to update
    let targetNote: PropertyNote | null = null;
    let targetParcelId: string | null = null;

    for (const [parcelId, notes] of state.notesByProperty) {
      const note = notes.find(n => n.id === noteId);
      if (note) {
        targetNote = note;
        targetParcelId = parcelId;
        break;
      }
    }

    if (!targetNote || !targetParcelId) return false;

    // Optimistic update
    const updatedNote = {
      ...targetNote,
      ...updates,
      updated_at: new Date().toISOString(),
    };

    setState(prev => {
      const newNotesByProperty = new Map(prev.notesByProperty);
      const existingNotes = newNotesByProperty.get(targetParcelId!) || [];
      const updatedNotes = existingNotes.map(note =>
        note.id === noteId ? updatedNote : note
      );
      newNotesByProperty.set(targetParcelId!, updatedNotes);

      return {
        ...prev,
        notesByProperty: newNotesByProperty,
      };
    });

    try {
      const { error } = await supabase
        .from('property_notes')
        .update(updates)
        .eq('id', noteId)
        .eq('user_id', user.id);

      if (error) throw error;

      toast({
        title: "Note Updated",
        description: "Your note has been updated successfully.",
        variant: "default",
      });

      return true;

    } catch (error: any) {
      console.error('Error updating note:', error);

      // Revert optimistic update
      setState(prev => {
        const newNotesByProperty = new Map(prev.notesByProperty);
        const existingNotes = newNotesByProperty.get(targetParcelId!) || [];
        const revertedNotes = existingNotes.map(note =>
          note.id === noteId ? targetNote! : note
        );
        newNotesByProperty.set(targetParcelId!, revertedNotes);

        return {
          ...prev,
          notesByProperty: newNotesByProperty,
        };
      });

      toast({
        title: "Error Updating Note",
        description: "Failed to update note. Please try again.",
        variant: "destructive",
      });

      return false;
    }
  }, [user?.id, state.notesByProperty, toast]);

  /**
   * Delete note
   */
  const deleteNote = useCallback(async (noteId: string) => {
    if (!user?.id) return false;

    // Find the note to delete
    let targetNote: PropertyNote | null = null;
    let targetParcelId: string | null = null;

    for (const [parcelId, notes] of state.notesByProperty) {
      const note = notes.find(n => n.id === noteId);
      if (note) {
        targetNote = note;
        targetParcelId = parcelId;
        break;
      }
    }

    if (!targetNote || !targetParcelId) return false;

    // Optimistic update
    setState(prev => {
      const newNotesByProperty = new Map(prev.notesByProperty);
      const existingNotes = newNotesByProperty.get(targetParcelId!) || [];
      const filteredNotes = existingNotes.filter(note => note.id !== noteId);

      if (filteredNotes.length === 0) {
        newNotesByProperty.delete(targetParcelId!);
      } else {
        newNotesByProperty.set(targetParcelId!, filteredNotes);
      }

      return {
        ...prev,
        notesByProperty: newNotesByProperty,
        totalCount: prev.totalCount - 1,
      };
    });

    try {
      const { error } = await supabase
        .from('property_notes')
        .delete()
        .eq('id', noteId)
        .eq('user_id', user.id);

      if (error) throw error;

      toast({
        title: "Note Deleted",
        description: "Your note has been deleted successfully.",
        variant: "default",
      });

      return true;

    } catch (error: any) {
      console.error('Error deleting note:', error);

      // Revert optimistic update
      setState(prev => {
        const newNotesByProperty = new Map(prev.notesByProperty);
        const existingNotes = newNotesByProperty.get(targetParcelId!) || [];
        const revertedNotes = [...existingNotes, targetNote!].sort((a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        newNotesByProperty.set(targetParcelId!, revertedNotes);

        return {
          ...prev,
          notesByProperty: newNotesByProperty,
          totalCount: prev.totalCount + 1,
        };
      });

      toast({
        title: "Error Deleting Note",
        description: "Failed to delete note. Please try again.",
        variant: "destructive",
      });

      return false;
    }
  }, [user?.id, state.notesByProperty, toast]);

  /**
   * Get notes by tag
   */
  const getNotesByTag = useCallback((tag: string): PropertyNote[] => {
    return allNotes.filter(note => note.tags.includes(tag));
  }, [allNotes]);

  /**
   * Get notes by type
   */
  const getNotesByType = useCallback((noteType: PropertyNote['note_type']): PropertyNote[] => {
    return allNotes.filter(note => note.note_type === noteType);
  }, [allNotes]);

  /**
   * Get unique tags across all notes
   */
  const getAllTags = useCallback((): string[] => {
    const tags = new Set<string>();
    allNotes.forEach(note => {
      note.tags.forEach(tag => tags.add(tag));
    });
    return Array.from(tags).sort();
  }, [allNotes]);

  // Set up real-time subscription
  useEffect(() => {
    if (!user?.id) return;

    // Set up real-time subscription
    const subscription = supabase
      .channel(`property-notes-${user.id}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'property_notes',
          filter: `user_id=eq.${user.id}`,
        },
        (payload) => {
          console.log('Property notes real-time update:', payload);

          const note = payload.new as PropertyNote;
          const oldNote = payload.old as PropertyNote;

          setState(prev => {
            const newNotesByProperty = new Map(prev.notesByProperty);

            switch (payload.eventType) {
              case 'INSERT':
                const existingNotes = newNotesByProperty.get(note.parcel_id) || [];
                newNotesByProperty.set(note.parcel_id, [note, ...existingNotes]);
                return {
                  ...prev,
                  notesByProperty: newNotesByProperty,
                  totalCount: prev.totalCount + 1,
                };

              case 'UPDATE':
                const updateNotes = newNotesByProperty.get(note.parcel_id) || [];
                const updatedNotes = updateNotes.map(n => n.id === note.id ? note : n);
                newNotesByProperty.set(note.parcel_id, updatedNotes);
                return {
                  ...prev,
                  notesByProperty: newNotesByProperty,
                };

              case 'DELETE':
                const deleteNotes = newNotesByProperty.get(oldNote.parcel_id) || [];
                const filteredNotes = deleteNotes.filter(n => n.id !== oldNote.id);

                if (filteredNotes.length === 0) {
                  newNotesByProperty.delete(oldNote.parcel_id);
                } else {
                  newNotesByProperty.set(oldNote.parcel_id, filteredNotes);
                }

                return {
                  ...prev,
                  notesByProperty: newNotesByProperty,
                  totalCount: prev.totalCount - 1,
                };

              default:
                return prev;
            }
          });
        }
      )
      .subscribe();

    // Cleanup subscription
    return () => {
      subscription.unsubscribe();
    };
  }, [user?.id]);

  // Fetch initial data when parcelId changes
  useEffect(() => {
    if (parcelId && user?.id && !state.notesByProperty.has(parcelId)) {
      fetchPropertyNotes(parcelId);
    }
  }, [parcelId, user?.id, state.notesByProperty, fetchPropertyNotes]);

  return {
    // State
    propertyNotes,
    allNotes,
    loading: state.loading,
    error: state.error,
    totalCount: state.totalCount,

    // Actions
    addNote,
    updateNote,
    deleteNote,
    fetchPropertyNotes,
    fetchAllNotes,
    getNotesByTag,
    getNotesByType,
    getAllTags,

    // Computed values
    hasNotes: propertyNotes.length > 0,
    noteCount: propertyNotes.length,
  };
};