/**
 * Tipi per Meeting
 */

export interface Participant {
    name: string;
    email: string;
}

export type MeetingType = 'internal' | 'external';

export interface Meeting {
    id: string;
    name: string;
    happenedAt: string;
    url?: string;
    organizer?: Participant;
    invitees: Participant[];
    template?: string;
    extraProperties?: Record<string, any>;
    meetingType?: MeetingType;

    // Campi sistema
    firebaseId?: string;
    hasTranscript: boolean;
    hasHighlights: boolean;
    videoUrl?: string;
    createdAt: string;
    updatedAt: string;
}

export interface MeetingCreate {
    name: string;
    url: string;
    happenedAt?: string;
    dryRun?: boolean;
}

export interface MeetingUpdate {
    name?: string;
    hasTranscript?: boolean;
    hasHighlights?: boolean;
    videoUrl?: string;
}

export interface MeetingList {
    page: number;
    pages: number;
    total: number;
    pageSize: number;
    results: Meeting[];
}

export interface MeetingFilters {
    query?: string;
    page?: number;
    limit?: number;
    dateFrom?: string;
    dateTo?: string;
    onlyParticipated?: boolean;
    meetingType?: MeetingType;
}