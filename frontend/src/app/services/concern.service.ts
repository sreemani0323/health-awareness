import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ApiConfigService } from './api-config.service';

export interface ConcernSubmission {
  category: string;
  state: string;
  district: string;
  municipality?: string;
  locality: string;
  description: string;
  duration: string;
  latitude?: number;
  longitude?: number;
  photo?: File;
  photos?: File[];
}

export interface ConcernSubmitResponse {
  message: string;
  notice: string;
  data: {
    reference_id: string;
    tracking_token: string;
    status: string;
    status_label: string;
    created_at: string;
  };
}

export interface ConcernTrackingData {
  reference_id: string;
  status: string;
  status_label: string;
  category: string;
  category_label: string;
  state: string;
  district: string;
  municipality: string;
  locality: string;
  description: string;
  duration: string;
  citizen_reply_requested: boolean;
  resolution_notes?: string;
  rejection_reason?: string;
  created_at: string;
  timeline: Array<{
    status: string;
    status_label: string;
    timestamp: string;
    public_notes?: string;
  }>;
  attachments: Array<{
    attachment_id: string;
    content_type: string;
    file_size_bytes: number;
    uploaded_at: string;
  }>;
}

export interface StaffMeResponse {
  data: {
    user_id: string;
    username: string;
    display_name: string;
    role: string;
    jurisdictions: Array<{
      state: string;
      district: string;
      municipality?: string;
    }>;
  };
}

@Injectable({
  providedIn: 'root',
})
export class ConcernService {
  private http = inject(HttpClient);
  private apiConfig = inject(ApiConfigService);
  private get apiUrl(): string {
    return this.apiConfig.getApiUrl('/concerns');
  }
  private get staffUrl(): string {
    return this.apiConfig.getApiUrl('/staff');
  }

  submitConcern(data: ConcernSubmission): Observable<ConcernSubmitResponse> {
    const formData = new FormData();
    formData.append('category', data.category);
    formData.append('state', data.state);
    formData.append('district', data.district);
    if (data.municipality) formData.append('municipality', data.municipality);
    formData.append('locality', data.locality);
    formData.append('description', data.description);
    formData.append('duration', data.duration);
    if (data.latitude) formData.append('latitude', data.latitude.toString());
    if (data.longitude) formData.append('longitude', data.longitude.toString());
    if (data.photos && data.photos.length > 0) {
      data.photos.forEach((file) => {
        formData.append('photos', file, file.name);
      });
    } else if (data.photo) {
      formData.append('photo', data.photo, data.photo.name);
    }

    return this.http.post<ConcernSubmitResponse>(this.apiUrl, formData, {
      withCredentials: true,
    });
  }

  trackConcern(referenceId: string, trackingToken: string): Observable<{ data: ConcernTrackingData }> {
    return this.http.post<{ data: ConcernTrackingData }>(
      `${this.apiUrl}/track`,
      { reference_id: referenceId, tracking_token: trackingToken },
      { withCredentials: true }
    );
  }

  replyToConcern(referenceId: string, trackingToken: string, replyText: string): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(
      `${this.apiUrl}/track/reply`,
      { reference_id: referenceId, tracking_token: trackingToken, reply_text: replyText },
      { withCredentials: true }
    );
  }

  // Staff endpoints
  getStaffMe(): Observable<StaffMeResponse> {
    return this.http.get<StaffMeResponse>(`${this.staffUrl}/me`, { withCredentials: true });
  }

  getStaffConcerns(filters?: { status?: string; category?: string; district?: string }): Observable<{ data: any[] }> {
    let params: any = {};
    if (filters?.status) params.status = filters.status;
    if (filters?.category) params.category = filters.category;
    if (filters?.district) params.district = filters.district;

    return this.http.get<{ data: any[] }>(`${this.staffUrl}/concerns`, {
      params,
      withCredentials: true,
    });
  }

  getStaffConcernDetail(reportId: string): Observable<{ data: any }> {
    return this.http.get<{ data: any }>(`${this.staffUrl}/concerns/${reportId}`, {
      withCredentials: true,
    });
  }

  updateStaffConcernStatus(reportId: string, update: {
    status: string;
    public_notes?: string;
    internal_notes?: string;
    rejection_reason?: string;
    resolution_notes?: string;
    citizen_reply_requested?: boolean;
  }): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(
      `${this.staffUrl}/concerns/${reportId}/status`,
      update,
      { withCredentials: true }
    );
  }

  assignHandler(reportId: string, handlerId: string, handlerName: string, jurisdiction?: string): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(
      `${this.staffUrl}/concerns/${reportId}/assign`,
      { handler_id: handlerId, handler_name: handlerName, jurisdiction },
      { withCredentials: true }
    );
  }

  getStaffHandlers(): Observable<{ data: any[] }> {
    return this.http.get<{ data: any[] }>(`${this.staffUrl}/handlers`, {
      withCredentials: true,
    });
  }
}
