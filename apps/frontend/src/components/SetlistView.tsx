'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import {
  ClockIcon,
  DocumentTextIcon,
  PencilIcon,
  TrashIcon,
  PlusIcon,
  CheckIcon,
  XMarkIcon,
  Bars3Icon,
} from '@heroicons/react/24/outline';
import { useWebSocket } from '@/lib/websocket';
import { apiService } from '@/lib/api';
import type { Setlist, SetlistItem } from '@/lib/api';

interface SetlistViewProps {
  setlist: Setlist;
  isEditable?: boolean;
  onUpdate?: (updatedSetlist: Setlist) => void;
  onDelete?: () => void;
}

interface EditingItem {
  index: number;
  title: string;
  key: string;
  duration: string;
  notes: string;
}

export default function SetlistView({
  setlist: initialSetlist,
  isEditable = false,
  onUpdate,
  onDelete,
}: SetlistViewProps) {
  const [setlist, setSetlist] = useState<Setlist>(initialSetlist);
  const [isEditing, setIsEditing] = useState(false);
  const [editingItem, setEditingItem] = useState<EditingItem | null>(null);
  const [isAddingItem, setIsAddingItem] = useState(false);
  const [newItem, setNewItem] = useState<Omit<SetlistItem, 'order_index'>>({
    title: '',
    key: '',
    estimated_duration: undefined,
    notes: '',
  });
  const [isSaving, setIsSaving] = useState(false);
  
  const { subscribe, unsubscribe } = useWebSocket();

  // Subscribe to real-time updates
  useEffect(() => {
    const unsubscribeSetlist = subscribe('setlist_updated', (data) => {
      if (data.setlist_id === setlist.id) {
        // Refresh setlist data
        apiService.getSetlist(setlist.id).then((updatedSetlist: Setlist) => {
          setSetlist(updatedSetlist);
          if (onUpdate) onUpdate(updatedSetlist);
        });
      }
    });

    return () => {
      unsubscribeSetlist();
    };
  }, [setlist.id, subscribe, unsubscribe, onUpdate]);

  // Handle drag and drop
  const handleDragEnd = useCallback(async (result: DropResult) => {
    if (!result.destination || !isEditable) return;

    const items = Array.from(setlist.items);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    // Update order indices
    const updatedItems = items.map((item, index) => ({
      ...item,
      order_index: index + 1,
    }));

    const updatedSetlist = { ...setlist, items: updatedItems };
    setSetlist(updatedSetlist);

    // Save to backend
    try {
      const saved = await apiService.updateSetlist(setlist.id, { items: updatedItems });
      setSetlist(saved);
      if (onUpdate) onUpdate(saved);
    } catch (error) {
      console.error('Failed to reorder items:', error);
      // Revert on error
      setSetlist(initialSetlist);
    }
  }, [setlist, initialSetlist, isEditable, onUpdate]);

  // Add new item
  const handleAddItem = useCallback(async () => {
    if (!newItem.title.trim()) return;

    setIsSaving(true);
    try {
      const items = [
        ...setlist.items,
        {
          ...newItem,
          order_index: setlist.items.length + 1,
          estimated_duration: newItem.estimated_duration || undefined,
        },
      ];

      const saved = await apiService.updateSetlist(setlist.id, { items });
      setSetlist(saved);
      if (onUpdate) onUpdate(saved);

      // Reset form
      setNewItem({
        title: '',
        key: '',
        estimated_duration: undefined,
        notes: '',
      });
      setIsAddingItem(false);
    } catch (error) {
      console.error('Failed to add item:', error);
    } finally {
      setIsSaving(false);
    }
  }, [setlist, newItem, onUpdate]);

  // Update item
  const handleUpdateItem = useCallback(async () => {
    if (!editingItem) return;

    setIsSaving(true);
    try {
      const items = [...setlist.items];
      items[editingItem.index] = {
        ...items[editingItem.index],
        title: editingItem.title,
        key: editingItem.key,
        estimated_duration: editingItem.duration ? parseInt(editingItem.duration) : undefined,
        notes: editingItem.notes,
      };

      const saved = await apiService.updateSetlist(setlist.id, { items });
      setSetlist(saved);
      if (onUpdate) onUpdate(saved);
      setEditingItem(null);
    } catch (error) {
      console.error('Failed to update item:', error);
    } finally {
      setIsSaving(false);
    }
  }, [setlist, editingItem, onUpdate]);

  // Delete item
  const handleDeleteItem = useCallback(async (index: number) => {
    if (!window.confirm('Are you sure you want to remove this item?')) return;

    try {
      const items = setlist.items
        .filter((_, i) => i !== index)
        .map((item, i) => ({ ...item, order_index: i + 1 }));

      const saved = await apiService.updateSetlist(setlist.id, { items });
      setSetlist(saved);
      if (onUpdate) onUpdate(saved);
    } catch (error) {
      console.error('Failed to delete item:', error);
    }
  }, [setlist, onUpdate]);

  // Calculate total duration
  const totalDuration = setlist.items.reduce(
    (total: number, item: SetlistItem) => total + (item.estimated_duration || 0),
    0
  );

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {setlist.name}
            </h2>
            {setlist.performance_date && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {new Date(setlist.performance_date).toLocaleDateString()} 
                {setlist.venue && ` • ${setlist.venue}`}
              </p>
            )}
            <div className="flex items-center mt-2 text-sm text-gray-600 dark:text-gray-400">
              <DocumentTextIcon className="h-4 w-4 mr-1" />
              <span>{setlist.items.length} songs</span>
              <ClockIcon className="h-4 w-4 ml-4 mr-1" />
              <span>{totalDuration} minutes</span>
            </div>
          </div>

          {isEditable && (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsEditing(!isEditing)}
                className={`px-3 py-1 text-sm font-medium rounded-lg transition-colors ${
                  isEditing
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                }`}
              >
                {isEditing ? 'Done' : 'Edit'}
              </button>
              {onDelete && (
                <button
                  onClick={onDelete}
                  className="p-1 text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                  aria-label="Delete setlist"
                >
                  <TrashIcon className="h-5 w-5" />
                </button>
              )}
            </div>
          )}
        </div>

        {setlist.notes && (
          <p className="mt-3 text-sm text-gray-600 dark:text-gray-400 italic">
            {setlist.notes}
          </p>
        )}
      </div>

      {/* Items List */}
      <DragDropContext onDragEnd={handleDragEnd}>
        <Droppable droppableId="setlist" isDropDisabled={!isEditing}>
          {(provided) => (
            <div
              {...provided.droppableProps}
              ref={provided.innerRef}
              className="divide-y divide-gray-200 dark:divide-gray-700"
            >
              {setlist.items.map((item, index) => (
                <Draggable
                  key={`${item.order_index}-${item.title}`}
                  draggableId={`${item.order_index}-${item.title}`}
                  index={index}
                  isDragDisabled={!isEditing}
                >
                  {(provided, snapshot) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.draggableProps}
                      className={`${
                        snapshot.isDragging
                          ? 'bg-blue-50 dark:bg-blue-900/20 shadow-lg'
                          : 'bg-white dark:bg-gray-800'
                      } transition-colors`}
                    >
                      {editingItem?.index === index ? (
                        // Edit Mode
                        <div className="p-4 space-y-3">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <input
                              type="text"
                              value={editingItem.title}
                              onChange={(e) =>
                                setEditingItem({ ...editingItem, title: e.target.value })
                              }
                              placeholder="Song title"
                              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                            />
                            <div className="flex space-x-3">
                              <input
                                type="text"
                                value={editingItem.key}
                                onChange={(e) =>
                                  setEditingItem({ ...editingItem, key: e.target.value })
                                }
                                placeholder="Key"
                                className="w-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                              />
                              <input
                                type="number"
                                value={editingItem.duration}
                                onChange={(e) =>
                                  setEditingItem({ ...editingItem, duration: e.target.value })
                                }
                                placeholder="Minutes"
                                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                              />
                            </div>
                          </div>
                          <input
                            type="text"
                            value={editingItem.notes}
                            onChange={(e) =>
                              setEditingItem({ ...editingItem, notes: e.target.value })
                            }
                            placeholder="Notes"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                          />
                          <div className="flex justify-end space-x-2">
                            <button
                              onClick={() => setEditingItem(null)}
                              className="p-2 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
                              disabled={isSaving}
                            >
                              <XMarkIcon className="h-5 w-5" />
                            </button>
                            <button
                              onClick={handleUpdateItem}
                              className="p-2 text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300"
                              disabled={isSaving}
                            >
                              <CheckIcon className="h-5 w-5" />
                            </button>
                          </div>
                        </div>
                      ) : (
                        // Display Mode
                        <div className="p-4 flex items-center">
                          {isEditing && (
                            <div
                              {...provided.dragHandleProps}
                              className="mr-3 text-gray-400 cursor-move"
                            >
                              <Bars3Icon className="h-5 w-5" />
                            </div>
                          )}

                          <div className="flex-1">
                            <div className="flex items-center">
                              <span className="text-sm font-medium text-gray-500 dark:text-gray-400 mr-3 min-w-[2rem]">
                                {item.order_index}.
                              </span>
                              <h3 className="font-medium text-gray-900 dark:text-white">
                                {item.title}
                              </h3>
                              {item.key && (
                                <span className="ml-3 px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded-full dark:bg-gray-700 dark:text-gray-300">
                                  {item.key}
                                </span>
                              )}
                              {item.estimated_duration && (
                                <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
                                  {item.estimated_duration}m
                                </span>
                              )}
                            </div>
                            {item.notes && (
                              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400 italic">
                                {item.notes}
                              </p>
                            )}
                          </div>

                          {isEditing && (
                            <div className="flex items-center space-x-2 ml-4">
                              <button
                                onClick={() =>
                                  setEditingItem({
                                    index,
                                    title: item.title,
                                    key: item.key || '',
                                    duration: item.estimated_duration?.toString() || '',
                                    notes: item.notes || '',
                                  })
                                }
                                className="p-1 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
                              >
                                <PencilIcon className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => handleDeleteItem(index)}
                                className="p-1 text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                              >
                                <TrashIcon className="h-4 w-4" />
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}

              {/* Add New Item */}
              {isEditing && (
                <div className="p-4">
                  {isAddingItem ? (
                    <div className="space-y-3">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <input
                          type="text"
                          value={newItem.title}
                          onChange={(e) =>
                            setNewItem({ ...newItem, title: e.target.value })
                          }
                          placeholder="Song title"
                          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                          autoFocus
                        />
                        <div className="flex space-x-3">
                          <input
                            type="text"
                            value={newItem.key || ''}
                            onChange={(e) =>
                              setNewItem({ ...newItem, key: e.target.value })
                            }
                            placeholder="Key"
                            className="w-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                          />
                          <input
                            type="number"
                            value={newItem.estimated_duration || ''}
                            onChange={(e) =>
                              setNewItem({
                                ...newItem,
                                estimated_duration: e.target.value
                                  ? parseInt(e.target.value)
                                  : undefined,
                              })
                            }
                            placeholder="Minutes"
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                          />
                        </div>
                      </div>
                      <input
                        type="text"
                        value={newItem.notes || ''}
                        onChange={(e) =>
                          setNewItem({ ...newItem, notes: e.target.value })
                        }
                        placeholder="Notes"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      />
                      <div className="flex justify-end space-x-2">
                        <button
                          onClick={() => {
                            setIsAddingItem(false);
                            setNewItem({
                              title: '',
                              key: '',
                              estimated_duration: undefined,
                              notes: '',
                            });
                          }}
                          className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-gray-800 dark:text-gray-300 dark:hover:text-gray-200"
                          disabled={isSaving}
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleAddItem}
                          className="px-3 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                          disabled={!newItem.title.trim() || isSaving}
                        >
                          Add Song
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => setIsAddingItem(true)}
                      className="flex items-center text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                    >
                      <PlusIcon className="h-5 w-5 mr-1" />
                      Add song
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
        </Droppable>
      </DragDropContext>
    </div>
  );
}