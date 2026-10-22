import { TestBed } from '@angular/core/testing';
import { SecureStorageService } from './secure-storage.service';

describe('SecureStorageService', () => {
  let service: SecureStorageService;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [SecureStorageService],
    });
    service = TestBed.inject(SecureStorageService);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should store and retrieve items in browser localStorage fallback', async () => {
    await service.setItem('test_token', 'jwt_val_123');
    const val = await service.getItem('test_token');
    expect(val).toBe('jwt_val_123');
  });

  it('should return null for non-existent keys', async () => {
    const val = await service.getItem('non_existent_key');
    expect(val).toBeNull();
  });

  it('should remove items correctly', async () => {
    await service.setItem('test_remove', 'to_delete');
    expect(await service.getItem('test_remove')).toBe('to_delete');
    await service.removeItem('test_remove');
    expect(await service.getItem('test_remove')).toBeNull();
  });

  it('should clear all stored items', async () => {
    await service.setItem('k1', 'v1');
    await service.setItem('k2', 'v2');
    await service.clear();
    expect(await service.getItem('k1')).toBeNull();
    expect(await service.getItem('k2')).toBeNull();
  });
});
